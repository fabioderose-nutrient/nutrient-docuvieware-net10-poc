using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc;

namespace MvcFrontend.Controllers
{
    public class HomeController : Controller
    {
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly IConfiguration _configuration;

        public HomeController(IHttpClientFactory httpClientFactory, IConfiguration configuration)
        {
            _httpClientFactory = httpClientFactory;
            _configuration = configuration;
        }

        // Base URL of the DocuViewareREST backend. The DocuVieware control markup embeds
        // absolute URLs derived from the backend's AppUri, so both must be a host the
        // BROWSER can reach (use the machine IP instead of localhost when browsing
        // from another machine).
        private string BackendBaseUrl => _configuration["BackendBaseUrl"] ?? "http://localhost:65088";

        public async Task<IActionResult> Index()
        {
            ViewBag.BackendBaseUrl = BackendBaseUrl;

            var configuration = new
            {
                // One DocuVieware session per page load: every visitor starts
                // with the default document.
                SessionId = Guid.NewGuid().ToString("N"),
                ControlId = "DocuVieware1",
                AllowPrint = true,
                EnablePrintButton = true,
                AllowUpload = true,
                EnableFileUploadButton = true,
                CollapsedSnapIn = true,
                ShowAnnotationsSnapIn = true,
                EnableRotateButtons = true,
                EnableZoomButtons = true,
                EnablePageViewButtons = true,
                EnableMultipleThumbnailSelection = true,
                EnableMouseModeButtons = true,
                EnableFormFieldsEdition = true,
                EnableTwainAcquisitionButton = false
            };

            var client = _httpClientFactory.CreateClient();
            using var content = new StringContent(JsonSerializer.Serialize(configuration), Encoding.UTF8, "application/json");
            using var response = await client.PostAsync(BackendBaseUrl + "/api/DocuViewareREST/GetDocuViewareControl", content);
            response.EnsureSuccessStatusCode();

            using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
            ViewBag.DocuViewareControlHtml = document.RootElement.GetProperty("htmlContent").GetString();

            return View();
        }
    }
}
