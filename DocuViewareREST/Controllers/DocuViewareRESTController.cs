using DocuViewareREST.Models;
using GdPicture14.WEB;
using Microsoft.AspNetCore.Mvc;

namespace DocuViewareREST.Controllers
{
    [ApiController]
    [Route("api/DocuViewareREST")]
    public class DocuViewareRESTController : ControllerBase
    {
        private const int SessionTimeoutMinutes = 20;
        private readonly IConfiguration _configuration;

        public DocuViewareRESTController(IConfiguration configuration)
        {
            _configuration = configuration;
        }

        /// <summary>
        /// Returns the control markup for the provided session and configuration.
        /// Freshly created sessions load the default document (from a URL).
        /// </summary>
        [HttpPost("GetDocuViewareControl")]
        public DocuViewareRESTOutputResponse GetDocuViewareControl(DocuViewareConfiguration controlConfiguration)
        {
            bool isNewSession = false;
            if (!DocuViewareManager.IsSessionAlive(controlConfiguration.SessionId))
            {
                if (string.IsNullOrEmpty(controlConfiguration.SessionId) || string.IsNullOrEmpty(controlConfiguration.ControlId))
                {
                    throw new Exception("Invalid session identifier and/or invalid control identifier.");
                }
                DocuViewareManager.CreateDocuViewareSession(controlConfiguration.SessionId, controlConfiguration.ControlId, SessionTimeoutMinutes);
                isNewSession = true;
            }

            using (DocuViewareControl docuVieware = new DocuViewareControl(controlConfiguration.SessionId))
            {
                docuVieware.AllowPrint = controlConfiguration.AllowPrint;
                docuVieware.EnablePrintButton = controlConfiguration.EnablePrintButton;
                docuVieware.AllowUpload = controlConfiguration.AllowUpload;
                docuVieware.EnableFileUploadButton = controlConfiguration.EnableFileUploadButton;
                docuVieware.CollapsedSnapIn = controlConfiguration.CollapsedSnapIn;
                docuVieware.ShowAnnotationsSnapIn = controlConfiguration.ShowAnnotationsSnapIn;
                docuVieware.EnableRotateButtons = controlConfiguration.EnableRotateButtons;
                docuVieware.EnableZoomButtons = controlConfiguration.EnableZoomButtons;
                docuVieware.EnablePageViewButtons = controlConfiguration.EnablePageViewButtons;
                docuVieware.EnableMultipleThumbnailSelection = controlConfiguration.EnableMultipleThumbnailSelection;
                docuVieware.EnableMouseModeButtons = controlConfiguration.EnableMouseModeButtons;
                docuVieware.EnableFormFieldsEdition = controlConfiguration.EnableFormFieldsEdition;
                docuVieware.EnableTwainAcquisitionButton = controlConfiguration.EnableTwainAcquisitionButton;
                docuVieware.MaxUploadSize = 36700160; // 35MB

                // Load the default document (from a URL) into freshly created sessions,
                // so the viewer never starts empty.
                if (isNewSession)
                {
                    string defaultDocumentUri = _configuration["DefaultDocumentUri"];
                    if (!string.IsNullOrEmpty(defaultDocumentUri))
                    {
                        docuVieware.LoadFromUri(new Uri(defaultDocumentUri));
                    }
                }

                using (StringWriter controlOutput = new StringWriter())
                {
                    docuVieware.RenderControl(controlOutput);
                    return new DocuViewareRESTOutputResponse { HtmlContent = controlOutput.ToString() };
                }
            }
        }

        /// <summary>
        /// Lists the documents available server side (App_Data/Documents).
        /// The client only ever sees file names; bytes stay on the server.
        /// </summary>
        [HttpGet("GetDocumentsList")]
        public string[] GetDocumentsList()
        {
            string documentsDirectory = CustomActions.DocumentsDirectory;
            if (!Directory.Exists(documentsDirectory)) { return Array.Empty<string>(); }
            return Directory.GetFiles(documentsDirectory)
                .Select(Path.GetFileName)
                .Where(name => !name.StartsWith('.'))
                .OrderBy(name => name)
                .ToArray();
        }

        /// <summary>
        /// Streams a server document. Used by the viewer's LoadFromUri: the DocuVieware
        /// SERVER fetches this URL itself, composes the document and sends rendered
        /// pages to the browser.
        /// </summary>
        [HttpGet("GetDocument/{name}")]
        public IActionResult GetDocument(string name)
        {
            string fileName = Path.GetFileName(name ?? "");
            string filePath = Path.Combine(CustomActions.DocumentsDirectory, fileName);
            if (string.IsNullOrEmpty(fileName) || !System.IO.File.Exists(filePath))
            {
                return NotFound();
            }
            // The file name in the URL (and this header) drives DocuVieware's format detection.
            Response.Headers.ContentDisposition = $"inline; filename=\"{fileName}\"";
            return File(System.IO.File.ReadAllBytes(filePath), ContentTypeFor(fileName));
        }

        private static string ContentTypeFor(string name) => Path.GetExtension(name).ToLowerInvariant() switch
        {
            ".pdf" => "application/pdf",
            ".xml" => "application/xml",
            ".eml" => "message/rfc822",
            ".msg" => "application/vnd.ms-outlook",
            ".txt" => "text/plain",
            _ => "application/octet-stream"
        };
    }
}
