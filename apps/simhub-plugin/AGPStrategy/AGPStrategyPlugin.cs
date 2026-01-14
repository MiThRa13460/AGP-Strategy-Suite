using System;
using System.Windows.Media;
using AGPStrategy.Models;
using GameReaderCommon;
using SimHub.Plugins;

namespace AGPStrategy
{
    /// <summary>
    /// AGP Strategy Suite Plugin for SimHub.
    ///
    /// Provides real-time telemetry analysis, setup recommendations,
    /// and strategy data from the AGP Strategy Suite application.
    /// </summary>
    [PluginDescription("AGP Strategy Suite integration - Real-time telemetry analysis and setup recommendations")]
    [PluginAuthor("AGP")]
    [PluginName("AGP Strategy Suite")]
    public class AGPStrategyPlugin : IPlugin, IDataPlugin, IWPFSettingsV2
    {
        /// <summary>
        /// Plugin settings instance.
        /// </summary>
        public AGPSettings Settings { get; private set; } = new AGPSettings();

        /// <summary>
        /// Instance of the data connector.
        /// </summary>
        private DataConnector? _connector;

        /// <summary>
        /// Instance of the property provider.
        /// </summary>
        private PropertyProvider? _propertyProvider;

        /// <summary>
        /// Plugin manager reference.
        /// </summary>
        private PluginManager? _pluginManager;

        /// <summary>
        /// Plugin display name.
        /// </summary>
        public string PluginName => "AGP Strategy Suite";

        /// <summary>
        /// Gets the left menu icon (for SimHub dark mode).
        /// </summary>
        public ImageSource PictureIcon
        {
            get
            {
                try
                {
                    return this.ToIcon(Properties.Resources.PluginIcon);
                }
                catch
                {
                    // Return null if icon resource is not available
                    return null!;
                }
            }
        }

        /// <summary>
        /// Gets the settings icon color.
        /// </summary>
        public string LeftMenuTitle => "AGP Strategy";

        /// <summary>
        /// Called once after plugins have been loaded.
        /// </summary>
        public void Init(PluginManager pluginManager)
        {
            _pluginManager = pluginManager;

            // Load settings
            Settings = this.ReadCommonSettings("AGPStrategySettings", () => new AGPSettings());

            // Initialize property provider
            _propertyProvider = new PropertyProvider(pluginManager);
            _propertyProvider.RegisterProperties();

            // Initialize data connector
            _connector = new DataConnector(Settings.BackendHost, Settings.BackendPort);
            _connector.DataReceived += OnDataReceived;
            _connector.ConnectionStateChanged += OnConnectionStateChanged;
            _connector.Error += OnError;

            // Auto-connect if enabled
            if (Settings.AutoConnect)
            {
                _connector.Connect();
            }

            SimHub.Logging.Current.Info("AGP Strategy Suite Plugin initialized");
        }

        /// <summary>
        /// Called at plugin end.
        /// </summary>
        public void End(PluginManager pluginManager)
        {
            // Save settings
            this.SaveCommonSettings("AGPStrategySettings", Settings);

            // Cleanup
            _connector?.Dispose();
            _connector = null;

            SimHub.Logging.Current.Info("AGP Strategy Suite Plugin ended");
        }

        /// <summary>
        /// Called every data update (usually 60Hz).
        /// </summary>
        public void DataUpdate(PluginManager pluginManager, ref GameData data)
        {
            // Properties are updated via WebSocket events
            // This method can be used for additional processing if needed

            // If game is running but not connected, try to reconnect
            if (data.GameRunning && !(_connector?.IsConnected ?? false) && Settings.AutoConnect)
            {
                _connector?.Connect();
            }
        }

        /// <summary>
        /// Gets the settings control for this plugin.
        /// </summary>
        public System.Windows.Controls.Control GetWPFSettingsControl(PluginManager pluginManager)
        {
            return new Settings.SettingsControl(this);
        }

        /// <summary>
        /// Connect to the AGP backend.
        /// </summary>
        public void Connect()
        {
            _connector?.Connect();
        }

        /// <summary>
        /// Disconnect from the AGP backend.
        /// </summary>
        public void Disconnect()
        {
            _connector?.Disconnect();
        }

        /// <summary>
        /// Gets whether the plugin is connected.
        /// </summary>
        public bool IsConnected => _connector?.IsConnected ?? false;

        /// <summary>
        /// Gets the current data from the backend.
        /// </summary>
        public AGPData? CurrentData => _connector?.CurrentData;

        private void OnDataReceived(object? sender, AGPData data)
        {
            _propertyProvider?.UpdateProperties(data);
        }

        private void OnConnectionStateChanged(object? sender, bool connected)
        {
            _pluginManager?.SetPropertyValue("AGP.Connected", connected);
            SimHub.Logging.Current.Info($"AGP Strategy Suite: {(connected ? "Connected" : "Disconnected")}");
        }

        private void OnError(object? sender, string error)
        {
            SimHub.Logging.Current.Error($"AGP Strategy Suite Error: {error}");
        }
    }

    /// <summary>
    /// Plugin settings.
    /// </summary>
    public class AGPSettings
    {
        /// <summary>
        /// Backend host address.
        /// </summary>
        public string BackendHost { get; set; } = "localhost";

        /// <summary>
        /// Backend port.
        /// </summary>
        public int BackendPort { get; set; } = 8765;

        /// <summary>
        /// Whether to auto-connect when SimHub starts.
        /// </summary>
        public bool AutoConnect { get; set; } = true;

        /// <summary>
        /// Whether to show notifications for recommendations.
        /// </summary>
        public bool ShowNotifications { get; set; } = true;

        /// <summary>
        /// Minimum priority for notifications (1=Critical, 5=Low).
        /// </summary>
        public int NotificationMinPriority { get; set; } = 2;
    }
}
