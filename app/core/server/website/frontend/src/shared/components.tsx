import { useState } from "react"

export interface TreeNode {
  id: string
  label: string
  icon?: string
  children?: TreeNode[]
  data?: unknown
}

interface TreeItemProps {
  node: TreeNode
  level?: number
  onSelect?: (node: TreeNode) => void
  selectedId?: string
}

function TreeItem({ node, level = 0, onSelect, selectedId }: TreeItemProps) {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = node.children && node.children.length > 0
  const isSelected = selectedId === node.id

  return (
    <div className="TreeNode" style={{ paddingLeft: `${level * 16}px` }}>
      <div
        className={`TreeNodeLabel ${isSelected ? "selected" : ""}`}
        onClick={() => {
          if (hasChildren) setExpanded(!expanded)
          onSelect?.(node)
        }}
      >
        {hasChildren && (
          <span className={`TreeToggle ${expanded ? "open" : ""}`}>
            <i className="fa-solid fa-chevron-right" />
          </span>
        )}
        {!hasChildren && <span className="TreeToggleSpacer" />}
        {node.icon && <span className={`TreeIcon ${node.icon}`} />}
        <span className="TreeLabel">{node.label}</span>
      </div>
      {hasChildren && expanded && (
        <div className="TreeChildren">
          {node.children!.map((child) => (
            <TreeItem
              key={child.id}
              node={child}
              level={level + 1}
              onSelect={onSelect}
              selectedId={selectedId}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface TreeProps {
  nodes: TreeNode[]
  onSelect?: (node: TreeNode) => void
  selectedId?: string
  className?: string
}

export function Tree({ nodes, onSelect, selectedId, className = "" }: TreeProps) {
  return (
    <div className={`Tree ${className}`}>
      {nodes.map((node) => (
        <TreeItem
          key={node.id}
          node={node}
          onSelect={onSelect}
          selectedId={selectedId}
        />
      ))}
    </div>
  )
}

export default Tree
