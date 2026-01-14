//! Overlay window management for AGP Strategy Suite
//!
//! This module handles creating and managing transparent overlay windows
//! that display telemetry, strategy, and standings information over the game.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Mutex;
use tauri::{AppHandle, Manager, WebviewUrl, WebviewWindowBuilder};

/// Overlay window configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OverlayConfig {
    pub id: String,
    pub title: String,
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
    pub visible: bool,
    pub opacity: f64,
    pub always_on_top: bool,
    pub click_through: bool,
}

impl Default for OverlayConfig {
    fn default() -> Self {
        Self {
            id: String::new(),
            title: String::from("Overlay"),
            x: 100,
            y: 100,
            width: 300,
            height: 200,
            visible: true,
            opacity: 1.0,
            always_on_top: true,
            click_through: false,
        }
    }
}

/// Preset overlay configurations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OverlayPreset {
    pub name: String,
    pub overlays: Vec<OverlayConfig>,
}

/// State for managing overlay windows
pub struct OverlayState {
    pub configs: Mutex<HashMap<String, OverlayConfig>>,
    pub presets: Mutex<Vec<OverlayPreset>>,
}

impl Default for OverlayState {
    fn default() -> Self {
        let mut configs = HashMap::new();

        // Default overlay configurations
        configs.insert(
            "telemetry".to_string(),
            OverlayConfig {
                id: "telemetry".to_string(),
                title: "Telemetrie".to_string(),
                x: 50,
                y: 50,
                width: 280,
                height: 180,
                visible: false,
                opacity: 0.9,
                always_on_top: true,
                click_through: true,
            },
        );

        configs.insert(
            "strategy".to_string(),
            OverlayConfig {
                id: "strategy".to_string(),
                title: "Strategie".to_string(),
                x: 50,
                y: 250,
                width: 320,
                height: 200,
                visible: false,
                opacity: 0.9,
                always_on_top: true,
                click_through: true,
            },
        );

        configs.insert(
            "standings".to_string(),
            OverlayConfig {
                id: "standings".to_string(),
                title: "Classement".to_string(),
                x: 1600,
                y: 50,
                width: 280,
                height: 400,
                visible: false,
                opacity: 0.9,
                always_on_top: true,
                click_through: true,
            },
        );

        // Default presets
        let presets = vec![
            OverlayPreset {
                name: "Course".to_string(),
                overlays: vec![
                    OverlayConfig {
                        id: "telemetry".to_string(),
                        visible: true,
                        x: 50,
                        y: 50,
                        ..Default::default()
                    },
                    OverlayConfig {
                        id: "strategy".to_string(),
                        visible: true,
                        x: 50,
                        y: 250,
                        ..Default::default()
                    },
                    OverlayConfig {
                        id: "standings".to_string(),
                        visible: true,
                        x: 1600,
                        y: 50,
                        ..Default::default()
                    },
                ],
            },
            OverlayPreset {
                name: "Qualifications".to_string(),
                overlays: vec![
                    OverlayConfig {
                        id: "telemetry".to_string(),
                        visible: true,
                        x: 50,
                        y: 50,
                        ..Default::default()
                    },
                    OverlayConfig {
                        id: "standings".to_string(),
                        visible: true,
                        x: 1600,
                        y: 50,
                        ..Default::default()
                    },
                ],
            },
            OverlayPreset {
                name: "Minimal".to_string(),
                overlays: vec![OverlayConfig {
                    id: "telemetry".to_string(),
                    visible: true,
                    x: 50,
                    y: 50,
                    ..Default::default()
                }],
            },
        ];

        Self {
            configs: Mutex::new(configs),
            presets: Mutex::new(presets),
        }
    }
}

/// Create an overlay window
#[tauri::command]
pub async fn create_overlay(
    app: AppHandle,
    state: tauri::State<'_, OverlayState>,
    overlay_id: String,
) -> Result<(), String> {
    let config = {
        let configs = state.configs.lock().map_err(|e| e.to_string())?;
        configs.get(&overlay_id).cloned()
    };

    let config = config.ok_or_else(|| format!("Overlay '{}' not found", overlay_id))?;

    // Check if window already exists
    if app.get_webview_window(&format!("overlay_{}", overlay_id)).is_some() {
        return Ok(());
    }

    // Build the overlay window
    let url = WebviewUrl::App(format!("/overlay/{}", overlay_id).into());

    let window = WebviewWindowBuilder::new(
        &app,
        format!("overlay_{}", overlay_id),
        url,
    )
    .title(&config.title)
    .inner_size(config.width as f64, config.height as f64)
    .position(config.x as f64, config.y as f64)
    .decorations(false)
    .transparent(true)
    .always_on_top(config.always_on_top)
    .skip_taskbar(true)
    .visible(config.visible)
    .resizable(false)
    .build()
    .map_err(|e| e.to_string())?;

    // Set click-through if enabled (Windows-specific)
    #[cfg(target_os = "windows")]
    if config.click_through {
        let _ = window.set_ignore_cursor_events(true);
    }

    Ok(())
}

/// Close an overlay window
#[tauri::command]
pub async fn close_overlay(app: AppHandle, overlay_id: String) -> Result<(), String> {
    if let Some(window) = app.get_webview_window(&format!("overlay_{}", overlay_id)) {
        window.close().map_err(|e| e.to_string())?;
    }
    Ok(())
}

/// Toggle overlay visibility
#[tauri::command]
pub async fn toggle_overlay(
    app: AppHandle,
    state: tauri::State<'_, OverlayState>,
    overlay_id: String,
) -> Result<bool, String> {
    let window_label = format!("overlay_{}", overlay_id);

    if let Some(window) = app.get_webview_window(&window_label) {
        let is_visible = window.is_visible().unwrap_or(false);
        if is_visible {
            window.hide().map_err(|e| e.to_string())?;
        } else {
            window.show().map_err(|e| e.to_string())?;
        }

        // Update config
        let mut configs = state.configs.lock().map_err(|e| e.to_string())?;
        if let Some(config) = configs.get_mut(&overlay_id) {
            config.visible = !is_visible;
        }

        return Ok(!is_visible);
    }

    // Window doesn't exist, create it
    create_overlay(app, state, overlay_id).await?;
    Ok(true)
}

/// Toggle all overlays
#[tauri::command]
pub async fn toggle_all_overlays(
    app: AppHandle,
    state: tauri::State<'_, OverlayState>,
    visible: bool,
) -> Result<(), String> {
    let overlay_ids: Vec<String> = {
        let configs = state.configs.lock().map_err(|e| e.to_string())?;
        configs.keys().cloned().collect()
    };

    for overlay_id in overlay_ids {
        let window_label = format!("overlay_{}", overlay_id);
        if let Some(window) = app.get_webview_window(&window_label) {
            if visible {
                window.show().map_err(|e| e.to_string())?;
            } else {
                window.hide().map_err(|e| e.to_string())?;
            }
        }
    }

    Ok(())
}

/// Update overlay configuration
#[tauri::command]
pub async fn update_overlay_config(
    app: AppHandle,
    state: tauri::State<'_, OverlayState>,
    config: OverlayConfig,
) -> Result<(), String> {
    // Update stored config
    {
        let mut configs = state.configs.lock().map_err(|e| e.to_string())?;
        configs.insert(config.id.clone(), config.clone());
    }

    // Update window if it exists
    let window_label = format!("overlay_{}", config.id);
    if let Some(window) = app.get_webview_window(&window_label) {
        window
            .set_position(tauri::Position::Physical(tauri::PhysicalPosition {
                x: config.x,
                y: config.y,
            }))
            .map_err(|e| e.to_string())?;

        window
            .set_size(tauri::Size::Physical(tauri::PhysicalSize {
                width: config.width,
                height: config.height,
            }))
            .map_err(|e| e.to_string())?;

        window
            .set_always_on_top(config.always_on_top)
            .map_err(|e| e.to_string())?;

        #[cfg(target_os = "windows")]
        {
            let _ = window.set_ignore_cursor_events(config.click_through);
        }

        if config.visible {
            window.show().map_err(|e| e.to_string())?;
        } else {
            window.hide().map_err(|e| e.to_string())?;
        }
    }

    Ok(())
}

/// Get all overlay configurations
#[tauri::command]
pub fn get_overlay_configs(
    state: tauri::State<'_, OverlayState>,
) -> Result<Vec<OverlayConfig>, String> {
    let configs = state.configs.lock().map_err(|e| e.to_string())?;
    Ok(configs.values().cloned().collect())
}

/// Get overlay presets
#[tauri::command]
pub fn get_overlay_presets(
    state: tauri::State<'_, OverlayState>,
) -> Result<Vec<OverlayPreset>, String> {
    let presets = state.presets.lock().map_err(|e| e.to_string())?;
    Ok(presets.clone())
}

/// Apply a preset
#[tauri::command]
pub async fn apply_overlay_preset(
    app: AppHandle,
    state: tauri::State<'_, OverlayState>,
    preset_name: String,
) -> Result<(), String> {
    let preset = {
        let presets = state.presets.lock().map_err(|e| e.to_string())?;
        presets.iter().find(|p| p.name == preset_name).cloned()
    };

    let preset = preset.ok_or_else(|| format!("Preset '{}' not found", preset_name))?;

    // First, hide all overlays
    toggle_all_overlays(app.clone(), state.clone(), false).await?;

    // Apply preset configurations
    for overlay_config in preset.overlays {
        update_overlay_config(app.clone(), state.clone(), overlay_config.clone()).await?;

        if overlay_config.visible {
            create_overlay(app.clone(), state.clone(), overlay_config.id.clone()).await?;
        }
    }

    Ok(())
}

/// Save current overlay positions as a preset
#[tauri::command]
pub fn save_overlay_preset(
    state: tauri::State<'_, OverlayState>,
    preset_name: String,
) -> Result<(), String> {
    let configs = state.configs.lock().map_err(|e| e.to_string())?;
    let mut presets = state.presets.lock().map_err(|e| e.to_string())?;

    let new_preset = OverlayPreset {
        name: preset_name.clone(),
        overlays: configs.values().cloned().collect(),
    };

    // Replace existing preset with same name or add new
    if let Some(existing) = presets.iter_mut().find(|p| p.name == preset_name) {
        *existing = new_preset;
    } else {
        presets.push(new_preset);
    }

    Ok(())
}

/// Set click-through mode for an overlay
#[tauri::command]
pub async fn set_overlay_click_through(
    app: AppHandle,
    state: tauri::State<'_, OverlayState>,
    overlay_id: String,
    click_through: bool,
) -> Result<(), String> {
    // Update config
    {
        let mut configs = state.configs.lock().map_err(|e| e.to_string())?;
        if let Some(config) = configs.get_mut(&overlay_id) {
            config.click_through = click_through;
        }
    }

    // Update window
    let window_label = format!("overlay_{}", overlay_id);
    if let Some(window) = app.get_webview_window(&window_label) {
        #[cfg(target_os = "windows")]
        {
            window
                .set_ignore_cursor_events(click_through)
                .map_err(|e| e.to_string())?;
        }
    }

    Ok(())
}
