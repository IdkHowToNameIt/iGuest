import { useState } from 'react'
import GridLayout, { WidthProvider } from 'react-grid-layout'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'
import Icon from './Icon.jsx'

const ResponsiveGrid = WidthProvider(GridLayout)

// Validate a layout loaded from localStorage against the current block set —
// if the shape doesn't match (corrupt value, or blocks changed since it was
// saved), fall back to the default so a stale value can never crash the grid.
function loadLayout(storageKey, blocks, defaultLayout) {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey))
    const keys = new Set(blocks.map((b) => b.key))
    if (
      Array.isArray(saved) &&
      saved.length === blocks.length &&
      saved.every(
        (item) =>
          item &&
          keys.has(item.i) &&
          Number.isFinite(item.x) &&
          Number.isFinite(item.y) &&
          Number.isFinite(item.w) &&
          Number.isFinite(item.h),
      )
    ) {
      return saved
    }
  } catch {
    /* corrupt/absent value — fall back to default */
  }
  return defaultLayout
}

// Reusable free-form block/widget dashboard: wraps react-grid-layout with
// localStorage persistence (per `storageKey`) and an "editing" flag that
// gates dragging/resizing so the layout can't be nudged by accident during
// normal use. Pass a changing `key` prop from the parent (e.g. bumped on
// "Reset layout") to force re-reading the (now-cleared) stored layout.
export default function DashboardGrid({
  storageKey,
  blocks,
  defaultLayout,
  editing,
  cols = 12,
  rowHeight = 56,
}) {
  const [layout, setLayout] = useState(() => loadLayout(storageKey, blocks, defaultLayout))

  function handleChange(next) {
    setLayout(next)
    localStorage.setItem(storageKey, JSON.stringify(next))
  }

  return (
    <ResponsiveGrid
      className={`widget-grid${editing ? ' editing' : ''}`}
      layout={layout}
      cols={cols}
      rowHeight={rowHeight}
      isDraggable={editing}
      isResizable={editing}
      draggableHandle=".widget-card-handle"
      onLayoutChange={handleChange}
      margin={[16, 16]}
    >
      {blocks.map((b) => (
        // `bare` blocks skip the card chrome: their content brings its own
        // surfaces (e.g. the stat-card row or the gradient promo card).
        <div key={b.key} className={`widget-card${b.bare ? ' widget-bare' : ''}`}>
          {editing && (
            <div className="widget-card-handle">
              <Icon name="grip" size={14} /> {b.title}
            </div>
          )}
          {b.content}
        </div>
      ))}
    </ResponsiveGrid>
  )
}

export function resetLayout(storageKey) {
  localStorage.removeItem(storageKey)
}
