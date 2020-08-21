const sendTelemetryData = () => {
  const url = "/telemetry/register-page-view/";
  const dataKeys = ["source_id", "path", "full_path", "method", "host", "port", "scheme"];

  let data = {};
  dataKeys.forEach((key) => {
    const attribute = `data-${key.replace("_", "-")}`;
    data[key] = $("#content-root").attr(attribute);
  });

  $.ajax({url, data});
};

const formatForms = () => {
  $('input[type=number]').addClass('form-control');
  $('input[type=password]').addClass('form-control');
  $('input[type=text]').addClass('form-control');
  $('input[type=email]').addClass('form-control');
  $('input[type=tel]').addClass('form-control');
  $('input[type=photo]').addClass('form-control');
  $('input[type=time]').addClass('form-control');
  $('input[type=date]').addClass('form-control');
  $('textarea').addClass('form-control').attr('rows', 4);
  $('select').addClass('form-control');
};

const formatArticle = () => {
  $('article img').addClass('img-responsive img-rounded');
};

$(() => {
  formatForms();
  formatArticle();
  sendTelemetryData();
});
