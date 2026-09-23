import { useRef, useState } from 'react'
import { IconCamera, IconTrash } from './Icons'

export default function PhotoDropzone({ files, onChange }) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef(null)

  function addFiles(fileList) {
    const incoming = Array.from(fileList).filter((f) => f.type.startsWith('image/'))
    if (incoming.length === 0) return
    onChange([...files, ...incoming])
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    addFiles(e.dataTransfer.files)
  }

  function removeAt(index) {
    onChange(files.filter((_, i) => i !== index))
  }

  return (
    <div>
      <div
        className={'dropzone' + (isDragging ? ' is-dragging' : '')}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter') inputRef.current?.click() }}
      >
        <IconCamera className="dropzone__icon" style={{ margin: '0 auto' }} />
        <div className="dropzone__title">Drop photos here, or click to choose</div>
        <div className="dropzone__sub">A clear photo of the issue helps it get resolved faster</div>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          hidden
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <div className="thumb-grid">
          {files.map((file, i) => (
            <Thumb key={i} file={file} onRemove={() => removeAt(i)} />
          ))}
        </div>
      )}
    </div>
  )
}

function Thumb({ file, onRemove }) {
  const url = URL.createObjectURL(file)
  return (
    <div className="thumb">
      <img src={url} alt="" onLoad={() => URL.revokeObjectURL(url)} />
      <button type="button" className="thumb__remove" onClick={onRemove} aria-label="Remove photo">
        <IconTrash />
      </button>
    </div>
  )
}
