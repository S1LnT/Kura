var csrftoken = $('meta[name=csrf-token]').attr('content')

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
    }
})
function runPythonFunc(func,value) {
  $.ajax({
      url: func,
      type: 'POST',
      data: { param: value}, // If you want to send additional data with the POST request
      success: function(o) {
          // Handle success response here
      },
      error: function(xhr, status, error) {
          // Handle error here
      }
  });
  return false;
}
