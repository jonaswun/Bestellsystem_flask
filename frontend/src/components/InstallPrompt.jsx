import { useEffect, useState } from 'react';

export default function InstallPrompt() {
  const [promptEvent, setPromptEvent] = useState(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handler = (event) => {
      event.preventDefault();
      setPromptEvent(event);
      setVisible(true);
    };

    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!promptEvent) return;
    promptEvent.prompt();
    const choiceResult = await promptEvent.userChoice;
    setVisible(false);
    setPromptEvent(null);
    if (choiceResult.outcome === 'accepted') {
      console.log('User accepted the install prompt');
    }
  };

  if (!visible) {
    return null;
  }

  return (
    <button className="install-button" onClick={handleInstall}>
      Installieren
    </button>
  );
}
