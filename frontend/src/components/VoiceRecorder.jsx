import { useRef, useState } from 'react'
import { IconMic, IconStop, IconTrash } from './Icons'

export default function VoiceRecorder({ clip, onChange }) {
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState('')
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  async function startRecording() {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        onChange(blob)
        stream.getTracks().forEach((t) => t.stop())
      }
      recorder.start()
      mediaRecorderRef.current = recorder
      setIsRecording(true)
    } catch {
      setError('Microphone access was blocked. Check your browser permissions to add a voice note.')
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
  }

  return (
    <div>
      <div className="recorder">
        <button
          type="button"
          className={'recorder__btn' + (isRecording ? ' is-recording' : '')}
          onClick={isRecording ? stopRecording : startRecording}
          aria-label={isRecording ? 'Stop recording' : 'Start voice note'}
        >
          {isRecording ? <IconStop /> : <IconMic />}
        </button>

        {isRecording && <span className="recorder__status">Recording…</span>}
        {!isRecording && clip && <span className="recorder__clip">Voice note attached ({Math.round(clip.size / 1024)} KB)</span>}
        {!isRecording && !clip && <span className="recorder__status">Optional — describe the issue by voice</span>}

        {clip && !isRecording && (
          <button type="button" className="thumb__remove" style={{ position: 'static', marginLeft: 'auto' }} onClick={() => onChange(null)} aria-label="Remove voice note">
            <IconTrash />
          </button>
        )}
      </div>
      {error && <div className="field__hint" style={{ color: 'var(--alert-red)' }}>{error}</div>}
    </div>
  )
}
