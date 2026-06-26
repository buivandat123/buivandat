import sys
import os
sys.path.append("/storage/emulated/0/download/kryzis")
os.chdir("/storage/emulated/0/download/kryzis")

from main import MainBot

try:
    bot = MainBot(
        api_key="api_key",
        secret_key="secret_key",
        imei="84b2fd2b-4db7-439f-97ca-8a05b205671d-a16ddaab909d2cf27fce353f26dd2ff2",
        session_cookies={"nl_b04af40bb0e193acf8a9877592394ada": "tzaoLC8i6lt5qJ5Ho2eG_iNLFqpOT72xbD8T1penVG", "zpdid": "41RxbrFsgJiG5v6KKlh4E1KTbvvH-i4s", "zlogin_session": "kW4JGLyjCnIxFnDDLXTbH-Tj2KLL4cz1xMuNKmHJOLccBmHQ25DeNwOc244UM7uC", "_zlang": "vn", "zpsid": "eMKnVcAlVqAZUYmFGw5m1yylUrLQe7G3pIraKK7TB0kC9Y0YHSbF2ByUI28mvJCtv3auOXAnS37uVpyb4l1LBFCh6GCVqt4qqYW150EhSoZLTImp79f35m", "__zi": "3000.QOBlzDCV2uGerkFzm0LJq6FNv_d21nxKOTYf-iSD6TTdtghx.1", "zpw_sek": "Ye_R.451751557.a0.YLRBUo1JVGMbVP0V0LDz1Ljn66u2QLz7PMSeRMa5Fszu10z0OX8KQ1SGILrNRa0dNIB4KNC5kW-oKiwB6Zbz1G"}
    )
    bot.settings = {"prefix": "("}
    bot._bot_enabled = True
    bot.listen()
except Exception as e:
    print(f"Bot lỗi: {e}")
    import traceback
    traceback.print_exc()
