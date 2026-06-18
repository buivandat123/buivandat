package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	_ "image/gif"
	_ "image/jpeg"
	"io"
	"math"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/chai2010/webp"
	xdraw "golang.org/x/image/draw"
	_ "golang.org/x/image/webp"
)

type options struct {
	ImageURL    string
	OutputPath  string
	Xp          bool
	MaxSize     int
	Radius      int
	Spin        bool
	Fps         int
	Scale       int
	Seconds     int
	Q           int
	SpinSeconds int
	SpinFps     int
	Sqr         bool
	ScaleFactor float64
	FfmpegPath  string
	WebpQuality float64
	RequestSec  int
	CommandSec  int
}

type mediaKind struct {
	Extension string `json:"extension"`
	Mime      string `json:"mime"`
}

func main() {
	opts := parseFlags()
	kind, err := createStickerURL(opts)
	if err != nil {
		fmt.Fprintln(os.Stderr, err.Error())
		os.Exit(1)
	}

	_ = json.NewEncoder(os.Stdout).Encode(kind)
}

func parseFlags() options {
	var opts options
	flag.StringVar(&opts.ImageURL, "url", "", "input image/video url")
	flag.StringVar(&opts.OutputPath, "out", "", "output webp path")
	flag.BoolVar(&opts.Xp, "xp", false, "remove background")
	flag.IntVar(&opts.MaxSize, "maxSize", 700, "max sticker size")
	flag.IntVar(&opts.Radius, "radius", 0, "round corner percent")
	flag.BoolVar(&opts.Spin, "spin", false, "create spinning sticker")
	flag.IntVar(&opts.Fps, "fps", 30, "animation fps")
	flag.IntVar(&opts.Scale, "scale", 480, "animation scale")
	flag.IntVar(&opts.Seconds, "seconds", 30, "animation seconds")
	flag.IntVar(&opts.Q, "q", 95, "webp quality for ffmpeg")
	flag.IntVar(&opts.SpinSeconds, "spinSeconds", 6, "spin seconds")
	flag.IntVar(&opts.SpinFps, "spinFps", 60, "spin fps")
	flag.BoolVar(&opts.Sqr, "sqr", false, "square mode")
	flag.Float64Var(&opts.ScaleFactor, "scaleFactor", 1.0, "square inner scale factor")
	flag.StringVar(&opts.FfmpegPath, "ffmpeg", "ffmpeg", "ffmpeg executable")
	flag.Float64Var((*float64)(&opts.WebpQuality), "webpQuality", 95, "webp quality")
	flag.IntVar(&opts.RequestSec, "requestTimeout", 15, "request timeout seconds")
	flag.IntVar(&opts.CommandSec, "commandTimeout", 180, "ffmpeg timeout seconds")
	flag.Parse()

	opts.MaxSize = max(1, opts.MaxSize)
	opts.Scale = max(1, opts.Scale)
	opts.Seconds = max(1, opts.Seconds)
	opts.Fps = max(1, opts.Fps)
	opts.Q = clampInt(opts.Q, 1, 100)
	opts.SpinSeconds = max(1, opts.SpinSeconds)
	opts.SpinFps = max(1, opts.SpinFps)
	opts.WebpQuality = float64(clampInt(int(opts.WebpQuality), 1, 100))
	opts.ScaleFactor = clampScale(opts.ScaleFactor)

	return opts
}

func createStickerURL(opts options) (mediaKind, error) {
	if strings.TrimSpace(opts.ImageURL) == "" {
		return mediaKind{}, errors.New("url is required")
	}
	if strings.TrimSpace(opts.OutputPath) == "" {
		return mediaKind{}, errors.New("out is required")
	}
	if opts.Xp {
		return mediaKind{}, errors.New("xp is not supported by go worker")
	}

	data, contentType, err := fetchBytes(opts.ImageURL, opts.RequestSec)
	if err != nil {
		return mediaKind{}, err
	}

	kind := guessKind(opts.ImageURL, contentType, data)
	if kind.Extension == "" {
		return mediaKind{}, errors.New("unsupported file format")
	}

	if kind.Extension == "jxl" {
		data, err = convertJxlToPngBytes(data, opts)
		if err != nil {
			return mediaKind{}, err
		}
		kind = mediaKind{Extension: "png", Mime: "image/png"}
	}

	isVideo := strings.HasPrefix(kind.Mime, "video/") || inSet(kind.Extension, "mp4", "mkv", "mov", "webm", "avi")
	isGif := kind.Extension == "gif"
	isWebp := kind.Extension == "webp"
	isAnimated := isGif || isVideo || isWebp

	if dir := filepath.Dir(opts.OutputPath); dir != "" && dir != "." {
		if err = os.MkdirAll(dir, 0o755); err != nil {
			return mediaKind{}, err
		}
	}

	if opts.Spin {
		return kind, runSpinPipeline(data, kind, isAnimated, opts)
	}

	if isWebp && opts.Radius == 0 && !opts.Sqr && opts.ScaleFactor >= 0.999 {
		if err = os.WriteFile(opts.OutputPath, data, 0o644); err != nil {
			return mediaKind{}, err
		}
		return kind, nil
	}

	if isAnimated && opts.Radius > 0 {
		return mediaKind{}, errors.New("animated radius is not supported by go worker")
	}

	if isAnimated {
		tmpIn, err := writeTmp(data, guessSuffix(kind))
		if err != nil {
			return mediaKind{}, err
		}
		defer os.Remove(tmpIn)

		if err = ffmpegToWebpAnim(tmpIn, opts.OutputPath, opts); err != nil {
			return mediaKind{}, err
		}
		return kind, nil
	}

	if err = bytesCreate(data, opts.OutputPath, opts.MaxSize, opts.Radius, opts.Sqr, opts.ScaleFactor, opts.WebpQuality); err != nil {
		return mediaKind{}, err
	}
	return kind, nil
}

func runSpinPipeline(data []byte, kind mediaKind, isAnimated bool, opts options) error {
	tmpA, err := os.CreateTemp("", "sticker-a-*.webp")
	if err != nil {
		return err
	}
	tmpAPath := tmpA.Name()
	_ = tmpA.Close()
	defer os.Remove(tmpAPath)

	tmpB, err := os.CreateTemp("", "sticker-b-*.webp")
	if err != nil {
		return err
	}
	tmpBPath := tmpB.Name()
	_ = tmpB.Close()
	defer os.Remove(tmpBPath)

	if isAnimated {
		if opts.Radius > 0 {
			return errors.New("animated radius with spin is not supported by go worker")
		}
		tmpIn, err2 := writeTmp(data, guessSuffix(kind))
		if err2 != nil {
			return err2
		}
		defer os.Remove(tmpIn)

		animOpts := opts
		animOpts.Fps = max(30, animOpts.Fps)
		if err2 = ffmpegToWebpAnim(tmpIn, tmpAPath, animOpts); err2 != nil {
			return err2
		}
	} else {
		rp := 100
		if opts.Sqr {
			rp = 0
		}
		if err = bytesCreate(data, tmpAPath, opts.MaxSize, rp, opts.Sqr, opts.ScaleFactor, opts.WebpQuality); err != nil {
			return err
		}
	}

	spinInput := tmpAPath
	if opts.Radius > 0 {
		if err = applyRoundStaticWebp(tmpAPath, tmpBPath, opts.Radius, opts.WebpQuality); err != nil {
			return err
		}
		spinInput = tmpBPath
	}

	return spinWebp(spinInput, opts.OutputPath, opts)
}

func fetchBytes(imageURL string, timeoutSec int) ([]byte, string, error) {
	client := &http.Client{Timeout: time.Duration(max(1, timeoutSec)) * time.Second}
	req, err := http.NewRequest(http.MethodGet, imageURL, nil)
	if err != nil {
		return nil, "", err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0")

	resp, err := client.Do(req)
	if err != nil {
		return nil, "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, "", errors.New(resp.Status)
	}

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, "", err
	}
	return data, resp.Header.Get("Content-Type"), nil
}

func guessKind(imageURL, contentType string, data []byte) mediaKind {
	mime := strings.TrimSpace(strings.ToLower(strings.Split(contentType, ";")[0]))
	if mime == "" && len(data) > 0 {
		mime = strings.ToLower(strings.TrimSpace(http.DetectContentType(data)))
	}
	if semi := strings.IndexByte(mime, ';'); semi >= 0 {
		mime = strings.TrimSpace(mime[:semi])
	}

	ext := ""
	if u, err := url.Parse(imageURL); err == nil {
		ext = strings.TrimPrefix(strings.ToLower(filepath.Ext(u.Path)), ".")
	}
	if ext == "jpeg" {
		ext = "jpg"
	}

	if ext == "" {
		ext = extFromMime(mime)
	}
	if mime == "" {
		mime = mimeFromExt(ext)
	}

	if ext == "" {
		return mediaKind{}
	}

	return mediaKind{Extension: ext, Mime: mime}
}

func extFromMime(mime string) string {
	switch mime {
	case "image/png":
		return "png"
	case "image/jpeg":
		return "jpg"
	case "image/webp":
		return "webp"
	case "image/gif":
		return "gif"
	case "image/jxl":
		return "jxl"
	case "video/mp4":
		return "mp4"
	case "video/webm":
		return "webm"
	case "video/quicktime":
		return "mov"
	case "video/x-matroska":
		return "mkv"
	case "video/x-msvideo":
		return "avi"
	default:
		if strings.HasPrefix(mime, "video/") {
			return "mp4"
		}
		return ""
	}
}

func mimeFromExt(ext string) string {
	switch ext {
	case "png":
		return "image/png"
	case "jpg", "jpeg":
		return "image/jpeg"
	case "webp":
		return "image/webp"
	case "gif":
		return "image/gif"
	case "jxl":
		return "image/jxl"
	case "mp4":
		return "video/mp4"
	case "webm":
		return "video/webm"
	case "mov":
		return "video/quicktime"
	case "mkv":
		return "video/x-matroska"
	case "avi":
		return "video/x-msvideo"
	default:
		return "application/octet-stream"
	}
}

func convertJxlToPngBytes(jxl []byte, opts options) ([]byte, error) {
	tmpIn, err := writeTmp(jxl, ".jxl")
	if err != nil {
		return nil, err
	}
	defer os.Remove(tmpIn)

	tmpOut := strings.TrimSuffix(tmpIn, ".jxl") + ".png"
	defer os.Remove(tmpOut)

	if err = runCmd([]string{opts.FfmpegPath, "-y", "-i", tmpIn, tmpOut}, opts.CommandSec); err != nil {
		return nil, err
	}

	return os.ReadFile(tmpOut)
}

func ffmpegToWebpAnim(inputPath, outputPath string, opts options) error {
	vf := ""
	if opts.Sqr {
		inner := max(1, int(float64(opts.Scale)*opts.ScaleFactor))
		vf = "fps=" + itoa(opts.Fps) + ",crop='min(iw,ih)':'min(iw,ih)',scale=" + itoa(inner) + ":" + itoa(inner) + ":flags=lanczos,pad=" + itoa(opts.Scale) + ":" + itoa(opts.Scale) + ":(ow-iw)/2:(oh-ih)/2:color=0x00000000"
	} else {
		vf = "fps=" + itoa(opts.Fps) + ",scale=" + itoa(opts.Scale) + ":-1:flags=lanczos"
	}

	cmd := []string{
		opts.FfmpegPath, "-y", "-i", inputPath,
		"-t", itoa(opts.Seconds),
		"-vf", vf,
		"-q:v", itoa(opts.Q),
		"-loop", "0",
		"-threads", "0",
		"-an",
		outputPath,
	}
	return runCmd(cmd, opts.CommandSec)
}

func spinWebp(inputPath, outputPath string, opts options) error {
	denom := max(1, opts.SpinFps*opts.SpinSeconds)
	cmd := []string{
		opts.FfmpegPath, "-y",
		"-loop", "1",
		"-i", inputPath,
		"-filter_complex", "fps=" + itoa(opts.SpinFps) + ",rotate=2*PI*n/" + itoa(denom) + ":c=none",
		"-t", itoa(opts.SpinSeconds),
		"-q:v", itoa(min(95, opts.Q)),
		"-loop", "0",
		"-threads", "0",
		"-an",
		outputPath,
	}
	return runCmd(cmd, opts.CommandSec)
}

func applyRoundStaticWebp(inputPath, outputPath string, radius int, q float64) error {
	in, err := os.ReadFile(inputPath)
	if err != nil {
		return err
	}
	img, _, err := image.Decode(bytes.NewReader(in))
	if err != nil {
		return err
	}
	out := applyRoundCorner(toNRGBA(img), radius)
	return saveWebp(outputPath, out, q)
}

func bytesCreate(imageBytes []byte, outputPath string, maxSize, radius int, sqr bool, scaleFactor float64, quality float64) error {
	img, _, err := image.Decode(bytes.NewReader(imageBytes))
	if err != nil {
		return err
	}

	out := processImage(img, maxSize, radius, sqr, scaleFactor)
	return saveWebp(outputPath, out, quality)
}

func processImage(img image.Image, maxSize, radius int, sqr bool, scaleFactor float64) image.Image {
	img = resizeKeepRatio(img, maxSize)

	if sqr {
		img = cropSquare(img)
		img = squareCanvas(img, maxSize, scaleFactor)
	} else if radius == 100 {
		img = cropSquare(img)
	}

	if radius > 0 {
		img = applyRoundCorner(toNRGBA(img), radius)
	}

	return img
}

func resizeKeepRatio(img image.Image, maxSize int) image.Image {
	b := img.Bounds()
	w, h := b.Dx(), b.Dy()
	m := max(w, h)
	if m <= maxSize {
		return toNRGBA(img)
	}

	s := float64(maxSize) / float64(m)
	nw := max(1, int(float64(w)*s))
	nh := max(1, int(float64(h)*s))

	dst := image.NewNRGBA(image.Rect(0, 0, nw, nh))
	xdraw.ApproxBiLinear.Scale(dst, dst.Bounds(), img, b, draw.Src, nil)
	return dst
}

func cropSquare(img image.Image) image.Image {
	b := img.Bounds()
	w, h := b.Dx(), b.Dy()
	s := min(w, h)
	x0 := b.Min.X + (w-s)/2
	y0 := b.Min.Y + (h-s)/2

	dst := image.NewNRGBA(image.Rect(0, 0, s, s))
	draw.Draw(dst, dst.Bounds(), img, image.Point{X: x0, Y: y0}, draw.Src)
	return dst
}

func squareCanvas(img image.Image, canvasSize int, scaleFactor float64) image.Image {
	sf := clampScale(scaleFactor)
	inner := max(1, int(float64(canvasSize)*sf))

	b := img.Bounds()
	w, h := b.Dx(), b.Dy()
	m := max(w, h)

	if m > inner {
		s := float64(inner) / float64(m)
		nw := max(1, int(float64(w)*s))
		nh := max(1, int(float64(h)*s))
		dst := image.NewNRGBA(image.Rect(0, 0, nw, nh))
		xdraw.ApproxBiLinear.Scale(dst, dst.Bounds(), img, b, draw.Src, nil)
		img = dst
		w, h = nw, nh
	}

	out := image.NewNRGBA(image.Rect(0, 0, canvasSize, canvasSize))
	x := (canvasSize - w) / 2
	y := (canvasSize - h) / 2
	draw.Draw(out, image.Rect(x, y, x+w, y+h), img, img.Bounds().Min, draw.Src)
	return out
}

func applyRoundCorner(src *image.NRGBA, percent int) *image.NRGBA {
	if percent <= 0 {
		return src
	}
	w := src.Bounds().Dx()
	h := src.Bounds().Dy()
	r := int(float64(min(w, h)) * float64(percent) / 200.0)
	if r <= 0 {
		return src
	}

	lim := min(w, h) / 2
	if r > lim {
		r = lim
	}

	out := image.NewNRGBA(image.Rect(0, 0, w, h))
	copy(out.Pix, src.Pix)

	rr := r * r
	x1 := w - r
	y1 := h - r

	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			if (x >= r && x < x1) || (y >= r && y < y1) {
				continue
			}

			cx := r
			if x >= x1 {
				cx = x1
			}
			cy := r
			if y >= y1 {
				cy = y1
			}

			dx := x - cx
			dy := y - cy
			if dx*dx+dy*dy <= rr {
				continue
			}

			i := y*out.Stride + x*4
			out.Pix[i+3] = 0
		}
	}

	return out
}

func toNRGBA(img image.Image) *image.NRGBA {
	if v, ok := img.(*image.NRGBA); ok && v.Rect.Min.X == 0 && v.Rect.Min.Y == 0 {
		return v
	}
	b := img.Bounds()
	dst := image.NewNRGBA(image.Rect(0, 0, b.Dx(), b.Dy()))
	draw.Draw(dst, dst.Bounds(), img, b.Min, draw.Src)
	return dst
}

func saveWebp(path string, img image.Image, quality float64) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	return webp.Encode(f, img, &webp.Options{Lossless: false, Quality: float32(quality)})
}

func runCmd(cmd []string, timeoutSec int) error {
	if len(cmd) == 0 {
		return errors.New("empty command")
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(max(1, timeoutSec))*time.Second)
	defer cancel()

	execCmd := exec.CommandContext(ctx, cmd[0], cmd[1:]...)
	execCmd.Stdout = io.Discard
	execCmd.Stderr = io.Discard
	if err := execCmd.Run(); err != nil {
		if ctx.Err() == context.DeadlineExceeded {
			return errors.New("command timeout: " + strings.Join(cmd, " "))
		}
		return err
	}
	return nil
}

func writeTmp(data []byte, suffix string) (string, error) {
	f, err := os.CreateTemp("", "sticker-*"+suffix)
	if err != nil {
		return "", err
	}
	path := f.Name()
	if _, err = f.Write(data); err != nil {
		_ = f.Close()
		_ = os.Remove(path)
		return "", err
	}
	if err = f.Close(); err != nil {
		_ = os.Remove(path)
		return "", err
	}
	return path, nil
}

func guessSuffix(kind mediaKind) string {
	switch kind.Extension {
	case "gif":
		return ".gif"
	case "webp":
		return ".webp"
	case "jpg", "jpeg":
		return ".jpg"
	case "png":
		return ".png"
	case "jxl":
		return ".jxl"
	case "mp4", "mkv", "mov", "webm", "avi":
		return "." + kind.Extension
	default:
		if strings.HasPrefix(kind.Mime, "video/") {
			return ".mp4"
		}
		if kind.Extension == "" {
			return ".bin"
		}
		return "." + kind.Extension
	}
}

func clampScale(v float64) float64 {
	if math.IsNaN(v) || math.IsInf(v, 0) {
		return 1
	}
	if v < 0.1 {
		return 0.1
	}
	if v > 1 {
		return 1
	}
	return v
}

func clampInt(v, lo, hi int) int {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}

func inSet(v string, set ...string) bool {
	for _, s := range set {
		if v == s {
			return true
		}
	}
	return false
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func itoa(v int) string { return strconv.Itoa(v) }

var _ color.Alpha
