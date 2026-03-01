// BastionCore.cs
// 
// Bastion C# Module Example
// 
// Demonstrates .NET integration patterns and Windows-specific security checks.
// This module can be used as a standalone library or integrated with the
// Python core via process invocation or gRPC.
//
// Build: dotnet build BastionCore.csproj
// Run:   dotnet run --project BastionCore.csproj

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace Bastion
{
    /// <summary>
    /// Main Bastion core class for .NET integration.
    /// Provides security checks and system information gathering.
    /// </summary>
    public class BastionCore
    {
        private readonly BastionConfig _config;
        private readonly BastionLogger _logger;

        /// <summary>
        /// Gets the version of Bastion.
        /// </summary>
        public const string Version = "1.0.0";

        /// <summary>
        /// Initializes a new instance of the BastionCore class.
        /// </summary>
        /// <param name="configPath">Optional path to configuration file</param>
        public BastionCore(string? configPath = null)
        {
            _config = BastionConfig.Load(configPath);
            _logger = new BastionLogger(_config.LogLevel);
        }

        /// <summary>
        /// Gather system information.
        /// </summary>
        /// <returns>System information dictionary</returns>
        public SystemInfo GetSystemInfo()
        {
            _logger.Info("Gathering system information");

            var info = new SystemInfo
            {
                Timestamp = DateTime.UtcNow,
                Platform = new PlatformInfo
                {
                    OS = Environment.OSVersion.ToString(),
                    Architecture = RuntimeInformation.ProcessArchitecture.ToString(),
                    Is64Bit = Environment.Is64BitProcess,
                    IsLinux = RuntimeInformation.IsOSPlatform(OSPlatform.Linux),
                    IsWindows = RuntimeInformation.IsOSPlatform(OSPlatform.Windows),
                    IsMacOS = RuntimeInformation.IsOSPlatform(OSPlatform.OSX),
                },
                Runtime = new RuntimeInfo
                {
                    Framework = RuntimeInformation.FrameworkDescription,
                    ProcessorCount = Environment.ProcessorCount,
                    WorkingSet = Environment.WorkingSet,
                    User = Environment.UserName,
                    MachineName = Environment.MachineName,
                },
                Security = new SecurityInfo
                {
                    IsElevated = IsElevated(),
                    IsDebuggerAttached = Debugger.IsAttached,
                }
            };

            _logger.Debug($"System info collected: {JsonSerializer.Serialize(info)}");
            return info;
        }

        /// <summary>
        /// Run security checks.
        /// </summary>
        /// <param name="level">Check level (basic, intermediate, advanced)</param>
        /// <returns>Security check results</returns>
        public SecurityResults RunSecurityCheck(string level = "basic")
        {
            _logger.Info($"Running {level} security check");

            var results = new SecurityResults
            {
                CheckLevel = level,
                Timestamp = DateTime.UtcNow,
                Checks = new List<CheckResult>(),
                Summary = new CheckSummary()
            };

            // Basic checks
            var checks = new List<Func<CheckResult>>
            {
                CheckAdministrator,
                CheckDotNetVersion,
                CheckTempDirectory,
            };

            // Intermediate checks
            if (level == "intermediate" || level == "advanced")
            {
                checks.Add(CheckEnvironmentVariables);
                checks.Add(CheckFilePermissions);
            }

            // Advanced checks
            if (level == "advanced")
            {
                checks.Add(CheckRunningProcesses);
                checks.Add(CheckNetworkConnections);
            }

            // Execute checks
            foreach (var check in checks)
            {
                try
                {
                    var result = check();
                    results.Checks.Add(result);
                    UpdateSummary(results.Summary, result);
                }
                catch (Exception ex)
                {
                    _logger.Error($"Check failed: {ex.Message}");
                    results.Checks.Add(new CheckResult
                    {
                        Name = check.Method.Name,
                        Status = "error",
                        Message = ex.Message
                    });
                    results.Summary.Failed++;
                }
            }

            _logger.Info($"Security check complete: {results.Summary.Passed} passed, " +
                        $"{results.Summary.Failed} failed, {results.Summary.Warnings} warnings");

            return results;
        }

        private CheckResult CheckAdministrator()
        {
            var isElevated = IsElevated();
            return new CheckResult
            {
                Name = "administrator_check",
                Status = isElevated ? "warning" : "passed",
                Message = isElevated ? "Running as administrator" : "Not running as administrator",
                Recommendation = isElevated ? "Avoid running as administrator unless necessary" : null
            };
        }

        private CheckResult CheckDotNetVersion()
        {
            var version = Environment.Version;
            var minVersion = new Version(6, 0);
            var passed = version >= minVersion;

            return new CheckResult
            {
                Name = "dotnet_version",
                Status = passed ? "passed" : "warning",
                Message = $".NET {version}",
                Recommendation = passed ? null : "Consider upgrading to .NET 6+"
            };
        }

        private CheckResult CheckTempDirectory()
        {
            var tempPath = Path.GetTempPath();
            var exists = Directory.Exists(tempPath);
            var writable = false;

            if (exists)
            {
                try
                {
                    var testFile = Path.Combine(tempPath, $"bastion_test_{Guid.NewGuid()}");
                    File.WriteAllText(testFile, "test");
                    File.Delete(testFile);
                    writable = true;
                }
                catch
                {
                    writable = false;
                }
            }

            return new CheckResult
            {
                Name = "temp_directory",
                Status = writable ? "passed" : "warning",
                Message = $"Temp path: {tempPath}, writable: {writable}"
            };
        }

        private CheckResult CheckEnvironmentVariables()
        {
            var sensitivePatterns = new[] { "PASSWORD", "SECRET", "KEY", "TOKEN" };
            var found = new List<string>();

            foreach (DictionaryEntry entry in Environment.GetEnvironmentVariables())
            {
                var key = entry.Key.ToString() ?? "";
                foreach (var pattern in sensitivePatterns)
                {
                    if (key.Contains(pattern, StringComparison.OrdinalIgnoreCase))
                    {
                        found.Add(key);
                        break;
                    }
                }
            }

            return new CheckResult
            {
                Name = "environment_variables",
                Status = found.Count > 0 ? "warning" : "passed",
                Message = found.Count > 0 
                    ? $"Found {found.Count} sensitive environment variables" 
                    : "No obvious sensitive environment variables",
                Details = found.Count > 0 ? found : null
            };
        }

        private CheckResult CheckFilePermissions()
        {
            var issues = new List<string>();
            var currentDir = Directory.GetCurrentDirectory();

            try
            {
                var files = Directory.GetFiles(currentDir);
                foreach (var file in files)
                {
                    // On Windows, check if file is world-writable
                    if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                    {
                        // Windows-specific permission check would go here
                        // This is a simplified example
                    }
                }
            }
            catch (UnauthorizedAccessException)
            {
                // Ignore permission errors
            }

            return new CheckResult
            {
                Name = "file_permissions",
                Status = issues.Count > 0 ? "warning" : "passed",
                Message = issues.Count > 0 
                    ? $"Found {issues.Count} permission issues" 
                    : "No obvious permission issues"
            };
        }

        private CheckResult CheckRunningProcesses()
        {
            var processes = Process.GetProcesses();
            return new CheckResult
            {
                Name = "running_processes",
                Status = "info",
                Message = $"Found {processes.Length} running processes",
                Details = processes.Take(20).Select(p => p.ProcessName).ToList()
            };
        }

        private CheckResult CheckNetworkConnections()
        {
            // This would use System.Net.NetworkInformation in a full implementation
            return new CheckResult
            {
                Name = "network_connections",
                Status = "info",
                Message = "Network connection check (placeholder)"
            };
        }

        private void UpdateSummary(CheckSummary summary, CheckResult result)
        {
            switch (result.Status)
            {
                case "passed":
                    summary.Passed++;
                    break;
                case "failed":
                    summary.Failed++;
                    break;
                case "warning":
                    summary.Warnings++;
                    break;
            }
        }

        /// <summary>
        /// Check if the current process is running with elevated privileges.
        /// </summary>
        /// <returns>True if elevated</returns>
        public static bool IsElevated()
        {
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                using var identity = WindowsIdentity.GetCurrent();
                var principal = new WindowsPrincipal(identity);
                return principal.IsInRole(WindowsBuiltInRole.Administrator);
            }

            if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux) ||
                RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
            {
                return Environment.GetEnvironmentVariable("USER") == "root" ||
                       Environment.GetEnvironmentVariable("HOME") == "/root";
            }

            return false;
        }

        /// <summary>
        /// Generate a report from security results.
        /// </summary>
        /// <param name="results">Security results</param>
        /// <param name="format">Output format (json, text)</param>
        /// <returns>Formatted report</returns>
        public string GenerateReport(SecurityResults results, string format = "json")
        {
            _logger.Info($"Generating {format} report");

            if (format == "json")
            {
                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
                };
                return JsonSerializer.Serialize(results, options);
            }

            // Text format
            var sb = new StringBuilder();
            sb.AppendLine("============================================================");
            sb.AppendLine("BASTION SECURITY REPORT");
            sb.AppendLine("============================================================");
            sb.AppendLine($"Generated: {DateTime.UtcNow:yyyy-MM-dd HH:mm:ss} UTC");
            sb.AppendLine($"Check Level: {results.CheckLevel}");
            sb.AppendLine();
            sb.AppendLine($"Summary: {results.Summary.Passed} passed, " +
                         $"{results.Summary.Failed} failed, " +
                         $"{results.Summary.Warnings} warnings");
            sb.AppendLine();
            sb.AppendLine("Checks:");
            foreach (var check in results.Checks)
            {
                sb.AppendLine($"  [{check.Status.ToUpper()}] {check.Name}: {check.Message}");
            }
            sb.AppendLine("============================================================");

            return sb.ToString();
        }
    }

    /// <summary>
    /// Configuration for Bastion.
    /// </summary>
    public class BastionConfig
    {
        public string LogLevel { get; set; } = "Information";
        public string OutputDir { get; set; } = "./reports";
        public List<string> Modules { get; set; } = new() { "core" };

        public static BastionConfig Load(string? path = null)
        {
            // Default configuration
            var config = new BastionConfig();

            // Try to load from file
            if (!string.IsNullOrEmpty(path) && File.Exists(path))
            {
                try
                {
                    var json = File.ReadAllText(path);
                    // In a full implementation, parse YAML or JSON config
                    _ = JsonSerializer.Deserialize<BastionConfig>(json);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Warning: Could not load config: {ex.Message}");
                }
            }

            return config;
        }
    }

    /// <summary>
    /// Logger for Bastion.
    /// </summary>
    public class BastionLogger
    {
        private readonly string _level;

        public BastionLogger(string level)
        {
            _level = level;
        }

        public void Debug(string message) => Log("DEBUG", message);
        public void Info(string message) => Log("INFO", message);
        public void Warning(string message) => Log("WARNING", message);
        public void Error(string message) => Log("ERROR", message);

        private void Log(string level, string message)
        {
            var levels = new[] { "DEBUG", "INFO", "WARNING", "ERROR" };
            var currentLevel = Array.IndexOf(levels, _level.ToUpper());
            var messageLevel = Array.IndexOf(levels, level);

            if (messageLevel >= currentLevel)
            {
                Console.WriteLine($"{DateTime.Now:yyyy-MM-dd HH:mm:ss} [{level}] {message}");
            }
        }
    }

    /// <summary>
    /// System information data structure.
    /// </summary>
    public class SystemInfo
    {
        public DateTime Timestamp { get; set; }
        public PlatformInfo Platform { get; set; } = new();
        public RuntimeInfo Runtime { get; set; } = new();
        public SecurityInfo Security { get; set; } = new();
    }

    public class PlatformInfo
    {
        public string OS { get; set; } = "";
        public string Architecture { get; set; } = "";
        public bool Is64Bit { get; set; }
        public bool IsLinux { get; set; }
        public bool IsWindows { get; set; }
        public bool IsMacOS { get; set; }
    }

    public class RuntimeInfo
    {
        public string Framework { get; set; } = "";
        public int ProcessorCount { get; set; }
        public long WorkingSet { get; set; }
        public string User { get; set; } = "";
        public string MachineName { get; set; } = "";
    }

    public class SecurityInfo
    {
        public bool IsElevated { get; set; }
        public bool IsDebuggerAttached { get; set; }
    }

    /// <summary>
    /// Security check results.
    /// </summary>
    public class SecurityResults
    {
        public string CheckLevel { get; set; } = "";
        public DateTime Timestamp { get; set; }
        public List<CheckResult> Checks { get; set; } = new();
        public CheckSummary Summary { get; set; } = new();
    }

    /// <summary>
    /// Individual check result.
    /// </summary>
    public class CheckResult
    {
        public string Name { get; set; } = "";
        public string Status { get; set; } = "";
        public string Message { get; set; } = "";
        public string? Recommendation { get; set; }
        public List<string>? Details { get; set; }
    }

    /// <summary>
    /// Check summary.
    /// </summary>
    public class CheckSummary
    {
        public int Passed { get; set; }
        public int Failed { get; set; }
        public int Warnings { get; set; }
    }

    /// <summary>
    /// Program entry point.
    /// </summary>
    class Program
    {
        static async Task Main(string[] args)
        {
            Console.WriteLine("Bastion .NET Module v" + BastionCore.Version);
            Console.WriteLine();

            var bastion = new BastionCore();

            // Get system info
            var sysInfo = bastion.GetSystemInfo();
            Console.WriteLine($"Platform: {sysInfo.Platform.OS}");
            Console.WriteLine($".NET: {sysInfo.Runtime.Framework}");
            Console.WriteLine();

            // Run security check
            var level = args.Length > 0 ? args[0] : "basic";
            var results = bastion.RunSecurityCheck(level);

            // Generate and print report
            var report = bastion.GenerateReport(results, "text");
            Console.WriteLine(report);

            await Task.CompletedTask;
        }
    }
}
