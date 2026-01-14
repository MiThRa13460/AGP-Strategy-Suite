using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace AGPStrategy.Settings
{
    /// <summary>
    /// Settings control for AGP Strategy Suite plugin.
    /// </summary>
    public partial class SettingsControl : UserControl
    {
        private readonly AGPStrategyPlugin _plugin;
        private bool _isInitializing = true;

        public SettingsControl(AGPStrategyPlugin plugin)
        {
            InitializeComponent();
            _plugin = plugin;

            // Load current settings
            LoadSettings();

            // Subscribe to connection state changes
            if (_plugin != null)
            {
                UpdateConnectionUI(_plugin.IsConnected);
            }

            _isInitializing = false;
        }

        private void LoadSettings()
        {
            if (_plugin?.Settings == null) return;

            HostInput.Text = _plugin.Settings.BackendHost;
            PortInput.Text = _plugin.Settings.BackendPort.ToString();
            AutoConnectCheckBox.IsChecked = _plugin.Settings.AutoConnect;
            ShowNotificationsCheckBox.IsChecked = _plugin.Settings.ShowNotifications;

            // Set priority combo box
            int priorityIndex = _plugin.Settings.NotificationMinPriority - 1;
            if (priorityIndex >= 0 && priorityIndex < PriorityComboBox.Items.Count)
            {
                PriorityComboBox.SelectedIndex = priorityIndex;
            }
        }

        private void UpdateConnectionUI(bool connected)
        {
            Dispatcher.Invoke(() =>
            {
                if (connected)
                {
                    StatusIndicator.Fill = new SolidColorBrush(Color.FromRgb(0x44, 0xFF, 0x44));
                    StatusText.Text = "Connected";
                    StatusDetails.Text = $"Connected to {_plugin.Settings.BackendHost}:{_plugin.Settings.BackendPort}";
                    ConnectButton.IsEnabled = false;
                    DisconnectButton.IsEnabled = true;
                }
                else
                {
                    StatusIndicator.Fill = new SolidColorBrush(Color.FromRgb(0xFF, 0x44, 0x44));
                    StatusText.Text = "Disconnected";
                    StatusDetails.Text = "Not connected to AGP backend";
                    ConnectButton.IsEnabled = true;
                    DisconnectButton.IsEnabled = false;
                }
            });
        }

        private void ConnectButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // Update settings before connecting
                _plugin.Settings.BackendHost = HostInput.Text;
                if (int.TryParse(PortInput.Text, out int port))
                {
                    _plugin.Settings.BackendPort = port;
                }

                _plugin.Connect();

                // Update UI after a short delay to allow connection
                var timer = new System.Windows.Threading.DispatcherTimer
                {
                    Interval = TimeSpan.FromMilliseconds(500)
                };
                timer.Tick += (s, args) =>
                {
                    timer.Stop();
                    UpdateConnectionUI(_plugin.IsConnected);
                };
                timer.Start();
            }
            catch (Exception ex)
            {
                StatusDetails.Text = $"Error: {ex.Message}";
            }
        }

        private void DisconnectButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                _plugin.Disconnect();
                UpdateConnectionUI(false);
            }
            catch (Exception ex)
            {
                StatusDetails.Text = $"Error: {ex.Message}";
            }
        }

        private void HostInput_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (_isInitializing || _plugin?.Settings == null) return;
            _plugin.Settings.BackendHost = HostInput.Text;
        }

        private void PortInput_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (_isInitializing || _plugin?.Settings == null) return;

            if (int.TryParse(PortInput.Text, out int port))
            {
                _plugin.Settings.BackendPort = port;
                PortInput.BorderBrush = new SolidColorBrush(Color.FromRgb(0x3D, 0x3D, 0x3D));
            }
            else
            {
                // Invalid input - show error border
                PortInput.BorderBrush = new SolidColorBrush(Color.FromRgb(0xFF, 0x44, 0x44));
            }
        }

        private void AutoConnectCheckBox_Changed(object sender, RoutedEventArgs e)
        {
            if (_isInitializing || _plugin?.Settings == null) return;
            _plugin.Settings.AutoConnect = AutoConnectCheckBox.IsChecked ?? true;
        }

        private void NotificationSettings_Changed(object sender, RoutedEventArgs e)
        {
            if (_isInitializing || _plugin?.Settings == null) return;
            _plugin.Settings.ShowNotifications = ShowNotificationsCheckBox.IsChecked ?? true;
        }

        private void PriorityComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (_isInitializing || _plugin?.Settings == null) return;

            if (PriorityComboBox.SelectedItem is ComboBoxItem item && item.Tag != null)
            {
                if (int.TryParse(item.Tag.ToString(), out int priority))
                {
                    _plugin.Settings.NotificationMinPriority = priority;
                }
            }
        }
    }
}
