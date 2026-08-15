import { useEffect, useState } from 'react';
import './InstallPrompt.css';

export default function InstallPrompt() {
  const [promptEvent, setPromptEvent] = useState(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Check if already running in standalone mode (installed PWA)
    const checkStandalone = 
      window.matchMedia('(display-mode: standalone)').matches ||
      window.navigator.standalone === true;

    setIsStandalone(checkStandalone);

    // Detect iOS
    const userAgent = window.navigator.userAgent.toLowerCase();
    const iosDevice = /iphone|ipad|ipod/.test(userAgent);
    setIsIOS(iosDevice);

    const handler = (event) => {
      event.preventDefault();
      setPromptEvent(event);
    };

    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!promptEvent) return;
    promptEvent.prompt();
    const choiceResult = await promptEvent.userChoice;
    setPromptEvent(null);
    if (choiceResult.outcome === 'accepted') {
      setDismissed(true);
    }
  };

  // Do not show if already installed (standalone mode) or dismissed
  if (isStandalone || dismissed) {
    return null;
  }

  // If beforeinstallprompt fired (Android/Chrome/Edge/Desktop)
  if (promptEvent) {
    return (
      <div className="install-banner">
        <div className="install-banner-content">
          <span className="install-icon">📱</span>
          <span>Als App installieren (Vollbild ohne Adressleiste)</span>
        </div>
        <div className="install-banner-actions">
          <button className="install-button" onClick={handleInstall}>
            Installieren
          </button>
          <button className="install-dismiss" onClick={() => setDismissed(true)}>✕</button>
        </div>
      </div>
    );
  }

  // iOS Safari specific banner
  if (isIOS) {
    return (
      <div className="install-banner ios-banner">
        <div className="install-banner-content">
          <span className="install-icon">📲</span>
          <span>
            Als App installieren: Tippe auf <strong>Teilen</strong> <span className="share-icon">⎋</span> und wähle <strong>"Zum Home-Bildschirm"</strong>.
          </span>
        </div>
        <button className="install-dismiss" onClick={() => setDismissed(true)}>✕</button>
      </div>
    );
  }

  return null;
}
