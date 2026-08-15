import { useState, useEffect } from 'react';

export default function FullscreenToggle() {
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => {
        console.error("Error attempting to enable fullscreen mode:", err);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  return (
    <button 
      onClick={toggleFullscreen}
      className="fullscreen-button"
      title={isFullscreen ? "Vollbild beenden" : "Vollbildmodus aktivieren"}
      style={{
        background: isFullscreen ? '#dc2626' : '#2563eb',
        color: '#ffffff',
        border: '1px solid rgba(255, 255, 255, 0.4)',
        borderRadius: '4px',
        padding: '4px 8px',
        cursor: 'pointer',
        fontSize: '12px',
        fontWeight: 'bold',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        boxShadow: '0 2px 5px rgba(0, 0, 0, 0.25)',
        marginLeft: '8px',
        whiteSpace: 'nowrap',
        flexShrink: 0
      }}
    >
      {isFullscreen ? '↘↙ Normal' : '⛶ Vollbild'}
    </button>
  );
}
