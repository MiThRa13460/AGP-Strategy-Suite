import { useState, useEffect, useCallback } from 'react';
import { check } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';
import { invoke } from '@tauri-apps/api/core';

export interface UpdateInfo {
  version: string;
  currentVersion: string;
  date: string;
  body: string; // Changelog/release notes
}

export interface UpdateProgress {
  downloaded: number;
  total: number;
  percent: number;
}

export type UpdateStatus =
  | 'idle'
  | 'checking'
  | 'available'
  | 'downloading'
  | 'ready'
  | 'error'
  | 'up-to-date';

interface UseUpdaterReturn {
  status: UpdateStatus;
  updateInfo: UpdateInfo | null;
  progress: UpdateProgress;
  error: string | null;
  checkForUpdates: () => Promise<void>;
  downloadUpdate: () => Promise<void>;
  installUpdate: () => Promise<void>;
  dismissUpdate: () => void;
}

export function useUpdater(): UseUpdaterReturn {
  const [status, setStatus] = useState<UpdateStatus>('idle');
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [progress, setProgress] = useState<UpdateProgress>({ downloaded: 0, total: 0, percent: 0 });
  const [error, setError] = useState<string | null>(null);
  const [updateObject, setUpdateObject] = useState<Awaited<ReturnType<typeof check>> | null>(null);

  // Get current version on mount
  useEffect(() => {
    const getCurrentVersion = async () => {
      try {
        const version = await invoke<string>('get_current_version');
        setUpdateInfo(prev => prev ? { ...prev, currentVersion: version } : null);
      } catch (e) {
        console.error('Failed to get current version:', e);
      }
    };
    getCurrentVersion();
  }, []);

  // Check for updates
  const checkForUpdates = useCallback(async () => {
    setStatus('checking');
    setError(null);

    try {
      const update = await check();

      if (update) {
        setUpdateObject(update);

        // Get current version
        const currentVersion = await invoke<string>('get_current_version');

        // Parse changelog from release body
        const changelog = update.body || 'No changelog available';

        setUpdateInfo({
          version: update.version,
          currentVersion,
          date: update.date || new Date().toISOString(),
          body: changelog,
        });

        setStatus('available');
      } else {
        setStatus('up-to-date');
        setUpdateInfo(null);
      }
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to check for updates';
      setError(errorMessage);
      setStatus('error');
      console.error('Update check failed:', e);
    }
  }, []);

  // Download update
  const downloadUpdate = useCallback(async () => {
    if (!updateObject) {
      setError('No update available');
      return;
    }

    setStatus('downloading');
    setProgress({ downloaded: 0, total: 0, percent: 0 });

    try {
      await updateObject.downloadAndInstall((event) => {
        switch (event.event) {
          case 'Started':
            setProgress({
              downloaded: 0,
              total: event.data.contentLength || 0,
              percent: 0,
            });
            break;
          case 'Progress':
            setProgress(prev => {
              const downloaded = prev.downloaded + event.data.chunkLength;
              const percent = prev.total > 0 ? Math.round((downloaded / prev.total) * 100) : 0;
              return { ...prev, downloaded, percent };
            });
            break;
          case 'Finished':
            setProgress(prev => ({ ...prev, percent: 100 }));
            setStatus('ready');
            break;
        }
      });
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to download update';
      setError(errorMessage);
      setStatus('error');
      console.error('Update download failed:', e);
    }
  }, [updateObject]);

  // Install update (relaunch app)
  const installUpdate = useCallback(async () => {
    try {
      await relaunch();
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to restart application';
      setError(errorMessage);
      setStatus('error');
      console.error('Relaunch failed:', e);
    }
  }, []);

  // Dismiss update notification
  const dismissUpdate = useCallback(() => {
    setStatus('idle');
    setUpdateInfo(null);
    setUpdateObject(null);
  }, []);

  // Auto-check for updates on mount (silent check)
  useEffect(() => {
    // Delay check by 3 seconds to let app initialize
    const timer = setTimeout(() => {
      checkForUpdates();
    }, 3000);

    return () => clearTimeout(timer);
  }, [checkForUpdates]);

  return {
    status,
    updateInfo,
    progress,
    error,
    checkForUpdates,
    downloadUpdate,
    installUpdate,
    dismissUpdate,
  };
}
