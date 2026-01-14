import React from 'react';
import { useUpdater, UpdateStatus } from '../hooks/useUpdater';
import {
  Download,
  RefreshCw,
  X,
  CheckCircle,
  AlertCircle,
  ArrowUpCircle,
  Loader2,
} from 'lucide-react';

interface UpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function UpdateModal({ isOpen, onClose }: UpdateModalProps) {
  const {
    status,
    updateInfo,
    progress,
    error,
    downloadUpdate,
    installUpdate,
    dismissUpdate,
  } = useUpdater();

  if (!isOpen) return null;

  const handleClose = () => {
    dismissUpdate();
    onClose();
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const parseChangelog = (body: string): React.ReactNode => {
    // Parse markdown-style changelog
    const lines = body.split('\n');
    const elements: React.ReactNode[] = [];

    lines.forEach((line, index) => {
      const trimmed = line.trim();

      if (trimmed.startsWith('## ')) {
        // H2 heading
        elements.push(
          <h3 key={index} className="text-lg font-semibold text-white mt-4 mb-2">
            {trimmed.slice(3)}
          </h3>
        );
      } else if (trimmed.startsWith('### ')) {
        // H3 heading
        elements.push(
          <h4 key={index} className="text-md font-medium text-gray-200 mt-3 mb-1">
            {trimmed.slice(4)}
          </h4>
        );
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        // List item
        elements.push(
          <li key={index} className="text-gray-300 ml-4 list-disc">
            {trimmed.slice(2)}
          </li>
        );
      } else if (trimmed.length > 0) {
        // Regular paragraph
        elements.push(
          <p key={index} className="text-gray-300 my-1">
            {trimmed}
          </p>
        );
      }
    });

    return <div className="space-y-1">{elements}</div>;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-gray-900 rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden border border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <ArrowUpCircle className="w-6 h-6 text-blue-400" />
            <h2 className="text-xl font-semibold text-white">Mise a jour disponible</h2>
          </div>
          <button
            onClick={handleClose}
            className="p-1 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {/* Version info */}
          {updateInfo && (
            <div className="mb-4">
              <div className="flex items-center gap-4 mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-gray-400 text-sm">Version actuelle:</span>
                  <span className="text-gray-300 font-mono">v{updateInfo.currentVersion}</span>
                </div>
                <span className="text-gray-600">→</span>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400 text-sm">Nouvelle version:</span>
                  <span className="text-green-400 font-mono font-semibold">v{updateInfo.version}</span>
                </div>
              </div>
              <span className="text-gray-500 text-xs">
                Publiee le {formatDate(updateInfo.date)}
              </span>
            </div>
          )}

          {/* Status-specific content */}
          {status === 'checking' && (
            <div className="flex items-center gap-3 py-8 justify-center">
              <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
              <span className="text-gray-300">Verification des mises a jour...</span>
            </div>
          )}

          {status === 'up-to-date' && (
            <div className="flex flex-col items-center gap-3 py-8">
              <CheckCircle className="w-12 h-12 text-green-400" />
              <span className="text-gray-300">Vous avez la derniere version!</span>
            </div>
          )}

          {status === 'error' && (
            <div className="flex flex-col items-center gap-3 py-8">
              <AlertCircle className="w-12 h-12 text-red-400" />
              <span className="text-gray-300">Erreur lors de la verification</span>
              {error && <span className="text-red-400 text-sm">{error}</span>}
            </div>
          )}

          {status === 'available' && updateInfo && (
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-2">Nouveautes:</h3>
              <div className="bg-gray-800/50 rounded-lg p-4 max-h-64 overflow-y-auto border border-gray-700">
                {parseChangelog(updateInfo.body)}
              </div>
            </div>
          )}

          {status === 'downloading' && (
            <div className="py-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-300 text-sm">Telechargement en cours...</span>
                <span className="text-gray-400 text-sm">{progress.percent}%</span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress.percent}%` }}
                />
              </div>

              {/* Downloaded size */}
              <div className="flex justify-between mt-2">
                <span className="text-gray-500 text-xs">
                  {formatBytes(progress.downloaded)} / {formatBytes(progress.total)}
                </span>
              </div>
            </div>
          )}

          {status === 'ready' && (
            <div className="flex flex-col items-center gap-3 py-6">
              <CheckCircle className="w-12 h-12 text-green-400" />
              <span className="text-gray-300">Mise a jour prete!</span>
              <span className="text-gray-500 text-sm">
                L'application va redemarrer pour appliquer la mise a jour.
              </span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-700 bg-gray-800/30">
          {status === 'available' && (
            <>
              <button
                onClick={handleClose}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Plus tard
              </button>
              <button
                onClick={downloadUpdate}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                Mettre a jour
              </button>
            </>
          )}

          {status === 'downloading' && (
            <button
              disabled
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-gray-400 rounded-lg cursor-not-allowed"
            >
              <Loader2 className="w-4 h-4 animate-spin" />
              Telechargement...
            </button>
          )}

          {status === 'ready' && (
            <>
              <button
                onClick={handleClose}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Plus tard
              </button>
              <button
                onClick={installUpdate}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Redemarrer
              </button>
            </>
          )}

          {(status === 'up-to-date' || status === 'error') && (
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Fermer
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// Auto-popup component that shows when update is available
export function UpdateNotification() {
  const { status, updateInfo } = useUpdater();
  const [dismissed, setDismissed] = React.useState(false);
  const [showModal, setShowModal] = React.useState(false);

  // Auto-show notification when update is available
  React.useEffect(() => {
    if (status === 'available' && !dismissed) {
      setShowModal(true);
    }
  }, [status, dismissed]);

  const handleClose = () => {
    setShowModal(false);
    setDismissed(true);
  };

  if (!showModal) return null;

  return <UpdateModal isOpen={showModal} onClose={handleClose} />;
}
