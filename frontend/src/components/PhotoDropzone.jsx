import { useRef, useState } from 'react'
import { IconCamera, IconTrash } from './Icons'

export default function PhotoDropzone({ files, onChange }) {
  const [isDragging, setIsDragging] = useState(false)
  const cameraRef = useRef(null)
  const galleryRef = useRef(null)

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
      {files.length === 0 ? (
        <div
          className={'dropzone' + (isDragging ? ' is-dragging' : '')}
          onClick={() => galleryRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter') galleryRef.current?.click() }}
        >
          <IconCamera className="dropzone__icon" style={{ margin: '0 auto' }} />
          <div className="dropzone__title">Drop photos here, or click to choose</div>
          <div className="dropzone__sub">A clear photo of the issue helps it get resolved faster</div>
        </div>
      ) : (
        <div className="photo-preview-grid">
          {files.map((file, i) => (
            <PreviewTile key={i} file={file} onRemove={() => removeAt(i)} />
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap' }}>
        <button type="button" className="photo-add-more" onClick={() => cameraRef.current?.click()}>
          <IconCamera width={18} height={18} />
          Take photo
        </button>
        <button type="button" className="photo-add-more" onClick={() => galleryRef.current?.click()}>
          <IconCamera width={18} height={18} />
          Choose from gallery
        </button>
      </div>

      {/* Opens the phone camera directly (on a computer it opens the file picker) */}
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        hidden
        onChange={(e) => { addFiles(e.target.files); e.target.value = '' }}
      />
      {/* Opens the gallery / file picker, several photos allowed */}
      <input
        ref={galleryRef}
        type="file"
        accept="image/*"
        multiple
        hidden
        onChange={(e) => { addFiles(e.target.files); e.target.value = '' }}
      />
    </div>
  )
}

function PreviewTile({ file, onRemove }) {
  const url = URL.createObjectURL(file)
  return (
    <div className="photo-preview-tile">
      <img src={url} alt="" onLoad={() => URL.revokeObjectURL(url)} />
      <button type="button" className="thumb__remove" onClick={onRemove} aria-label="Remove photo">
        <IconTrash />
      </button>
    </div>
  )
}
