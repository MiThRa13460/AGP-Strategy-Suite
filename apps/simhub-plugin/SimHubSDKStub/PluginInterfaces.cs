using System;
using System.Windows.Controls;
using System.Windows.Media;
using GameReaderCommon;

namespace SimHub.Plugins
{
    /// <summary>
    /// Base plugin interface.
    /// </summary>
    public interface IPlugin
    {
        /// <summary>
        /// Called when plugin is initialized.
        /// </summary>
        void Init(PluginManager pluginManager);

        /// <summary>
        /// Called when plugin is ended.
        /// </summary>
        void End(PluginManager pluginManager);
    }

    /// <summary>
    /// Data plugin interface for real-time updates.
    /// </summary>
    public interface IDataPlugin : IPlugin
    {
        /// <summary>
        /// Called every data update (usually 60Hz).
        /// </summary>
        void DataUpdate(PluginManager pluginManager, ref GameData data);
    }

    /// <summary>
    /// WPF Settings interface v2.
    /// </summary>
    public interface IWPFSettingsV2
    {
        /// <summary>
        /// Gets the plugin icon.
        /// </summary>
        ImageSource PictureIcon { get; }

        /// <summary>
        /// Gets the left menu title.
        /// </summary>
        string LeftMenuTitle { get; }

        /// <summary>
        /// Gets the settings control.
        /// </summary>
        Control GetWPFSettingsControl(PluginManager pluginManager);
    }

    /// <summary>
    /// Plugin description attribute.
    /// </summary>
    [AttributeUsage(AttributeTargets.Class)]
    public class PluginDescriptionAttribute : Attribute
    {
        public string Description { get; }
        public PluginDescriptionAttribute(string description) => Description = description;
    }

    /// <summary>
    /// Plugin author attribute.
    /// </summary>
    [AttributeUsage(AttributeTargets.Class)]
    public class PluginAuthorAttribute : Attribute
    {
        public string Author { get; }
        public PluginAuthorAttribute(string author) => Author = author;
    }

    /// <summary>
    /// Plugin name attribute.
    /// </summary>
    [AttributeUsage(AttributeTargets.Class)]
    public class PluginNameAttribute : Attribute
    {
        public string Name { get; }
        public PluginNameAttribute(string name) => Name = name;
    }

    /// <summary>
    /// Plugin manager class.
    /// </summary>
    public class PluginManager
    {
        /// <summary>
        /// Adds a property to SimHub.
        /// </summary>
        public void AddProperty(string name, Type type, object defaultValue) { }

        /// <summary>
        /// Sets a property value.
        /// </summary>
        public void SetPropertyValue(string name, object value) { }

        /// <summary>
        /// Gets a property value.
        /// </summary>
        public object? GetPropertyValue(string name) => null;
    }

    /// <summary>
    /// Plugin extensions.
    /// </summary>
    public static class PluginExtensions
    {
        /// <summary>
        /// Converts a bitmap to an ImageSource.
        /// </summary>
        public static ImageSource ToIcon(this IWPFSettingsV2 plugin, System.Drawing.Bitmap? bitmap)
        {
            return null!;
        }

        /// <summary>
        /// Reads common settings.
        /// </summary>
        public static T ReadCommonSettings<T>(this IPlugin plugin, string name, Func<T> defaultValue) where T : class
        {
            return defaultValue();
        }

        /// <summary>
        /// Saves common settings.
        /// </summary>
        public static void SaveCommonSettings<T>(this IPlugin plugin, string name, T settings) where T : class
        {
        }
    }
}

namespace SimHub
{
    /// <summary>
    /// SimHub logging class.
    /// </summary>
    public static class Logging
    {
        /// <summary>
        /// Current logger instance.
        /// </summary>
        public static ILogger Current { get; } = new Logger();
    }

    /// <summary>
    /// Logger interface.
    /// </summary>
    public interface ILogger
    {
        void Info(string message);
        void Error(string message);
        void Warn(string message);
        void Debug(string message);
    }

    /// <summary>
    /// Default logger implementation.
    /// </summary>
    internal class Logger : ILogger
    {
        public void Info(string message) { }
        public void Error(string message) { }
        public void Warn(string message) { }
        public void Debug(string message) { }
    }
}
