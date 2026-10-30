// ============================================================================
//  DocuVieware MVC frontend - .NET 10
//  Stands in for your own application: calls the DocuVieware REST backend,
//  receives the control HTML and injects it into a Razor view.
// ============================================================================

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllersWithViews();
builder.Services.AddHttpClient();

var app = builder.Build();
app.UseStaticFiles();
app.UseRouting();
app.MapControllerRoute(name: "default", pattern: "{controller=Home}/{action=Index}/{id?}");

// Address of this frontend (FrontendUrl in appsettings.json or the environment).
app.Run(app.Configuration["FrontendUrl"] ?? "http://localhost:8090");
