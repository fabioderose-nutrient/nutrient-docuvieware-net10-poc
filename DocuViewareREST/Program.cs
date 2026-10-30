using GdPicture14;
using GdPicture14.WEB;

// ============================================================================
//  DocuVieware REST backend - .NET 10 (DocuVieware.API, cross-platform)
//  Hosts the DocuVieware control server side: sessions, rendering, streaming.
//  The browser only ever receives rendered pages, never the document bytes.
// ============================================================================

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllers();
builder.Services.AddCors(options => options.AddDefaultPolicy(policy =>
    policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()));

var app = builder.Build();
app.UseCors();
app.UseStaticFiles(); // serves wwwroot (default document URL target)
app.MapControllers();

// Public base URL of THIS backend: it is embedded in the control markup, so it
// must be reachable by the browser (use the machine IP/hostname when browsing
// from another machine). Configured in appsettings.json or the AppUri
// environment variable.
string appUri = app.Configuration["AppUri"] ?? "http://localhost:65088";

DocuViewareREST.CustomActions.DocumentsDirectory = Path.Combine(app.Environment.ContentRootPath, "App_Data", "Documents");

// License key from DOCUVIEWARE_LICENSE_KEY. An empty key starts evaluation mode
// (RegisterKEY must still be called).
DocuViewareLicensing.RegisterKEY(Environment.GetEnvironmentVariable("DOCUVIEWARE_LICENSE_KEY") ?? "");
DocuViewareManager.SetupConfiguration(
    true,
    DocuViewareSessionStateMode.File,
    Path.Combine(app.Environment.ContentRootPath, "Cache"),
    appUri,
    "api/docuvieware3");
DocuViewareEventsHandler.CustomAction += DocuViewareREST.CustomActions.Handle;

app.Run(appUri);

namespace DocuViewareREST
{
    /// <summary>
    /// Custom actions posted from the client with DocuViewareAPI.PostCustomServerAction.
    /// "loadServerFile": streams a server-side file into the viewer session. XML is not
    /// a native viewer format, so it is loaded under a .txt name (the DocumentName
    /// parameter of LoadFromStream drives format detection) and rendered as text.
    /// </summary>
    public static class CustomActions
    {
        private static readonly HashSet<string> SupportedExtensions = new(StringComparer.OrdinalIgnoreCase)
        {
            ".pdf",
            ".doc", ".docx", ".rtf", ".odt",
            ".xls", ".xlsx", ".ods", ".csv",
            ".ppt", ".pptx",
            ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp",
            ".eml", ".msg",
            ".txt"
        };

        public static string DocumentsDirectory { get; set; }

        public static void Handle(object sender, CustomActionEventArgs e)
        {
            if (e.actionName != "loadServerFile") { return; }

            string fileName = e.args != null ? Path.GetFileName(e.args.ToString()) : null;
            if (string.IsNullOrEmpty(fileName))
            {
                e.result = "ERROR: no file name provided.";
                return;
            }

            string filePath = Path.Combine(DocumentsDirectory, fileName);
            if (!File.Exists(filePath))
            {
                e.result = "ERROR: file not found: " + fileName;
                return;
            }

            string documentName = fileName;
            string extension = Path.GetExtension(fileName);
            if (!SupportedExtensions.Contains(extension))
            {
                if (extension.Equals(".xml", StringComparison.OrdinalIgnoreCase))
                {
                    documentName = Path.ChangeExtension(fileName, ".txt");
                }
                else
                {
                    e.result = "ERROR: unsupported file type: " + extension;
                    return;
                }
            }

            GdPictureStatus status = e.docuVieware.LoadFromStream(File.OpenRead(filePath), true, documentName, "", "");
            e.result = status == GdPictureStatus.OK ? "OK:" + documentName : "ERROR: " + status;
        }
    }
}
