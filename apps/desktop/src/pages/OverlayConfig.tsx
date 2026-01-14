import { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { MiniTelemetry, MiniStrategy, MiniStandings } from '../components/overlay'

interface OverlayConfig {
  id: string
  title: string
  x: number
  y: number
  width: number
  height: number
  visible: boolean
  opacity: number
  always_on_top: boolean
  click_through: boolean
}

interface OverlayPreset {
  name: string
  overlays: OverlayConfig[]
}

export function OverlayConfigPage() {
  const [overlays, setOverlays] = useState<OverlayConfig[]>([])
  const [presets, setPresets] = useState<OverlayPreset[]>([])
  const [selectedOverlay, setSelectedOverlay] = useState<string | null>(null)
  const [newPresetName, setNewPresetName] = useState('')

  // Load configs on mount
  useEffect(() => {
    loadConfigs()
    loadPresets()
  }, [])

  const loadConfigs = async () => {
    try {
      const configs = await invoke<OverlayConfig[]>('get_overlay_configs')
      setOverlays(configs)
    } catch (error) {
      console.error('Failed to load overlay configs:', error)
      // Use default configs for development
      setOverlays([
        { id: 'telemetry', title: 'Telemetrie', x: 50, y: 50, width: 280, height: 180, visible: false, opacity: 0.9, always_on_top: true, click_through: true },
        { id: 'strategy', title: 'Strategie', x: 50, y: 250, width: 320, height: 200, visible: false, opacity: 0.9, always_on_top: true, click_through: true },
        { id: 'standings', title: 'Classement', x: 1600, y: 50, width: 280, height: 400, visible: false, opacity: 0.9, always_on_top: true, click_through: true },
      ])
    }
  }

  const loadPresets = async () => {
    try {
      const presetList = await invoke<OverlayPreset[]>('get_overlay_presets')
      setPresets(presetList)
    } catch (error) {
      console.error('Failed to load presets:', error)
      setPresets([
        { name: 'Course', overlays: [] },
        { name: 'Qualifications', overlays: [] },
        { name: 'Minimal', overlays: [] },
      ])
    }
  }

  const toggleOverlay = async (id: string) => {
    try {
      const newVisible = await invoke<boolean>('toggle_overlay', { overlayId: id })
      setOverlays(prev =>
        prev.map(o => o.id === id ? { ...o, visible: newVisible } : o)
      )
    } catch (error) {
      console.error('Failed to toggle overlay:', error)
      // Update locally for development
      setOverlays(prev =>
        prev.map(o => o.id === id ? { ...o, visible: !o.visible } : o)
      )
    }
  }

  const updateConfig = async (config: OverlayConfig) => {
    try {
      await invoke('update_overlay_config', { config })
      setOverlays(prev =>
        prev.map(o => o.id === config.id ? config : o)
      )
    } catch (error) {
      console.error('Failed to update config:', error)
      setOverlays(prev =>
        prev.map(o => o.id === config.id ? config : o)
      )
    }
  }

  const applyPreset = async (presetName: string) => {
    try {
      await invoke('apply_overlay_preset', { presetName })
      await loadConfigs()
    } catch (error) {
      console.error('Failed to apply preset:', error)
    }
  }

  const savePreset = async () => {
    if (!newPresetName.trim()) return
    try {
      await invoke('save_overlay_preset', { presetName: newPresetName })
      await loadPresets()
      setNewPresetName('')
    } catch (error) {
      console.error('Failed to save preset:', error)
    }
  }

  const toggleAllOverlays = async (visible: boolean) => {
    try {
      await invoke('toggle_all_overlays', { visible })
      setOverlays(prev => prev.map(o => ({ ...o, visible })))
    } catch (error) {
      console.error('Failed to toggle all overlays:', error)
      setOverlays(prev => prev.map(o => ({ ...o, visible })))
    }
  }

  const selectedConfig = overlays.find(o => o.id === selectedOverlay)

  return (
    <div className="min-h-screen bg-agp-bg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Configuration Overlays</h1>
          <p className="text-sm text-gray-500">Configurez les overlays in-game</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => toggleAllOverlays(true)}
            className="px-4 py-2 bg-agp-accent text-black rounded-lg text-sm font-medium hover:bg-agp-accent/80 transition-colors"
          >
            Afficher tout
          </button>
          <button
            onClick={() => toggleAllOverlays(false)}
            className="px-4 py-2 bg-agp-card border border-agp-border text-white rounded-lg text-sm hover:bg-agp-border transition-colors"
          >
            Masquer tout
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Left: Overlay list and previews */}
        <div className="col-span-8 space-y-6">
          {/* Overlay cards */}
          <div className="grid grid-cols-3 gap-4">
            {overlays.map((overlay) => (
              <OverlayCard
                key={overlay.id}
                config={overlay}
                isSelected={selectedOverlay === overlay.id}
                onSelect={() => setSelectedOverlay(overlay.id)}
                onToggle={() => toggleOverlay(overlay.id)}
              />
            ))}
          </div>

          {/* Preview */}
          <div className="bg-agp-card border border-agp-border rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-4">Apercu</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="aspect-video bg-black/50 rounded-lg overflow-hidden p-2">
                <MiniTelemetry />
              </div>
              <div className="aspect-video bg-black/50 rounded-lg overflow-hidden p-2">
                <MiniStrategy />
              </div>
              <div className="aspect-[3/4] bg-black/50 rounded-lg overflow-hidden p-2">
                <MiniStandings />
              </div>
            </div>
          </div>

          {/* Hotkeys info */}
          <div className="bg-agp-card border border-agp-border rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-4">Raccourcis clavier</h3>
            <div className="grid grid-cols-4 gap-4">
              <HotkeyInfo hotkey="F1" action="Toggle tous les overlays" />
              <HotkeyInfo hotkey="F2" action="Toggle Telemetrie" />
              <HotkeyInfo hotkey="F3" action="Toggle Strategie" />
              <HotkeyInfo hotkey="F4" action="Toggle Classement" />
            </div>
          </div>
        </div>

        {/* Right: Settings panel */}
        <div className="col-span-4 space-y-6">
          {/* Presets */}
          <div className="bg-agp-card border border-agp-border rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-4">Presets</h3>
            <div className="space-y-2 mb-4">
              {presets.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => applyPreset(preset.name)}
                  className="w-full px-4 py-2 bg-black/30 hover:bg-agp-border rounded-lg text-left text-sm text-white transition-colors"
                >
                  {preset.name}
                </button>
              ))}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={newPresetName}
                onChange={(e) => setNewPresetName(e.target.value)}
                placeholder="Nom du preset"
                className="flex-1 px-3 py-2 bg-black/30 border border-agp-border rounded-lg text-sm text-white placeholder-gray-600 focus:outline-none focus:border-agp-accent"
              />
              <button
                onClick={savePreset}
                disabled={!newPresetName.trim()}
                className="px-4 py-2 bg-agp-accent text-black rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Sauver
              </button>
            </div>
          </div>

          {/* Selected overlay settings */}
          {selectedConfig && (
            <div className="bg-agp-card border border-agp-border rounded-lg p-6">
              <h3 className="text-sm text-gray-400 mb-4">
                Parametres - {selectedConfig.title}
              </h3>

              <div className="space-y-4">
                {/* Position */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">Position X</label>
                    <input
                      type="number"
                      value={selectedConfig.x}
                      onChange={(e) => updateConfig({ ...selectedConfig, x: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 bg-black/30 border border-agp-border rounded-lg text-sm text-white focus:outline-none focus:border-agp-accent"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">Position Y</label>
                    <input
                      type="number"
                      value={selectedConfig.y}
                      onChange={(e) => updateConfig({ ...selectedConfig, y: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 bg-black/30 border border-agp-border rounded-lg text-sm text-white focus:outline-none focus:border-agp-accent"
                    />
                  </div>
                </div>

                {/* Size */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">Largeur</label>
                    <input
                      type="number"
                      value={selectedConfig.width}
                      onChange={(e) => updateConfig({ ...selectedConfig, width: parseInt(e.target.value) || 100 })}
                      className="w-full px-3 py-2 bg-black/30 border border-agp-border rounded-lg text-sm text-white focus:outline-none focus:border-agp-accent"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">Hauteur</label>
                    <input
                      type="number"
                      value={selectedConfig.height}
                      onChange={(e) => updateConfig({ ...selectedConfig, height: parseInt(e.target.value) || 100 })}
                      className="w-full px-3 py-2 bg-black/30 border border-agp-border rounded-lg text-sm text-white focus:outline-none focus:border-agp-accent"
                    />
                  </div>
                </div>

                {/* Opacity */}
                <div>
                  <label className="text-xs text-gray-500 block mb-1">
                    Opacite: {Math.round(selectedConfig.opacity * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0.3"
                    max="1"
                    step="0.05"
                    value={selectedConfig.opacity}
                    onChange={(e) => updateConfig({ ...selectedConfig, opacity: parseFloat(e.target.value) })}
                    className="w-full accent-agp-accent"
                  />
                </div>

                {/* Toggles */}
                <div className="space-y-3">
                  <ToggleSetting
                    label="Toujours au premier plan"
                    checked={selectedConfig.always_on_top}
                    onChange={(checked) => updateConfig({ ...selectedConfig, always_on_top: checked })}
                  />
                  <ToggleSetting
                    label="Click-through (ignore les clics)"
                    checked={selectedConfig.click_through}
                    onChange={(checked) => updateConfig({ ...selectedConfig, click_through: checked })}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Tips */}
          <div className="bg-agp-card border border-agp-border rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-3">Conseils</h3>
            <ul className="space-y-2 text-xs text-gray-500">
              <li className="flex items-start gap-2">
                <span className="text-agp-accent">*</span>
                <span>Activez "Click-through" pour interagir avec le jeu a travers l'overlay</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-agp-accent">*</span>
                <span>Utilisez les presets pour basculer rapidement entre configurations</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-agp-accent">*</span>
                <span>Les positions sont sauvegardees automatiquement</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

interface OverlayCardProps {
  config: OverlayConfig
  isSelected: boolean
  onSelect: () => void
  onToggle: () => void
}

function OverlayCard({ config, isSelected, onSelect, onToggle }: OverlayCardProps) {
  return (
    <div
      onClick={onSelect}
      className={`bg-agp-card border rounded-lg p-4 cursor-pointer transition-all ${
        isSelected ? 'border-agp-accent' : 'border-agp-border hover:border-gray-600'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-white font-medium">{config.title}</h4>
        <button
          onClick={(e) => { e.stopPropagation(); onToggle() }}
          className={`w-10 h-5 rounded-full transition-colors relative ${
            config.visible ? 'bg-agp-accent' : 'bg-gray-700'
          }`}
        >
          <div
            className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${
              config.visible ? 'left-5' : 'left-0.5'
            }`}
          />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="text-gray-500">Position</div>
        <div className="text-gray-400 text-right">{config.x}, {config.y}</div>
        <div className="text-gray-500">Taille</div>
        <div className="text-gray-400 text-right">{config.width}x{config.height}</div>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${config.visible ? 'bg-agp-success' : 'bg-gray-600'}`} />
        <span className="text-xs text-gray-500">
          {config.visible ? 'Visible' : 'Masque'}
        </span>
      </div>
    </div>
  )
}

function HotkeyInfo({ hotkey, action }: { hotkey: string; action: string }) {
  return (
    <div className="flex items-center gap-3">
      <kbd className="px-2 py-1 bg-black/50 border border-agp-border rounded text-xs text-agp-accent font-mono">
        {hotkey}
      </kbd>
      <span className="text-xs text-gray-400">{action}</span>
    </div>
  )
}

interface ToggleSettingProps {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
}

function ToggleSetting({ label, checked, onChange }: ToggleSettingProps) {
  return (
    <label className="flex items-center justify-between cursor-pointer">
      <span className="text-sm text-gray-400">{label}</span>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={`w-10 h-5 rounded-full transition-colors relative ${
          checked ? 'bg-agp-accent' : 'bg-gray-700'
        }`}
      >
        <div
          className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${
            checked ? 'left-5' : 'left-0.5'
          }`}
        />
      </button>
    </label>
  )
}

export default OverlayConfigPage
