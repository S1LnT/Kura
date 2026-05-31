function initializeMediaElements() {
  function secondsToMinutes(time) {
    var minutes = Math.floor(time / 60); 
    var seconds = Math.floor(time % 60); 
    seconds = ("0" + (+seconds + 1)).slice(-2);
    return minutes + ":" + seconds;
  }

  $('.audio-player audio').mediaelementplayer({
      alwaysShowControls: false,
      features: [],
      audioVolume: 'horizontal',
      iPadUseNativeControls: true,
      iPhoneUseNativeControls: true,
      AndroidUseNativeControls: true,
      success: function(mediaElement, domObject) {
          mediaElement.addEventListener('timeupdate', function(e) {
              var parent = $(this).closest('.audio-player');
              var currentTime = mediaElement.currentTime;
              var duration = mediaElement.duration;
              
              if (isFinite(duration) && duration > 0) {
                  var percentage = (currentTime / duration) * 100 + "%";
                  if (currentTime > 0.5 && currentTime <= duration) {
                      parent.find(".progress-bar").css("width", percentage); 
                      parent.find('.song-current-time').html(secondsToMinutes(currentTime) + ' / ');
                  }
              }
          }, false);

          mediaElement.addEventListener('loadedmetadata', function(e) {
              var parent = $(this).closest('.audio-player');
              var duration = mediaElement.duration;
              
              if (isFinite(duration) && duration > 0) {
                  parent.find('.song-duration').html(secondsToMinutes(duration));
              }
          });

          mediaElement.addEventListener('canplay', function(e) {
              var parent = $(this).closest('.audio-player');
              var playButton = parent.find('.playpause');
              var duration = mediaElement.duration;

              if (isFinite(duration) && duration > 0) {
                  parent.find('.song-duration').html(secondsToMinutes(duration));
              }
              
              playButton.prop('disabled', false);

              playButton.on('click', function(e) {
                  e.stopPropagation(); 
                  if (parent.hasClass('is-paused')) {
                      mediaElement.play();
                  } else if (parent.hasClass('is-playing')) {
                      mediaElement.pause();
                  }
              });
          });

          mediaElement.addEventListener('ended', function(e) {
              var parent = $(this).closest('.audio-player');
              parent.find(".progress-bar").css("width", "100%");
              parent.find('.playpause').removeClass('is-playing').addClass('is-paused');
              parent.find('.playpause').find('#play-btn').attr("src","static/images/audiojs/play.svg")
              parent.removeClass('is-playing').addClass('is-paused').addClass('already-played');
          });

          mediaElement.addEventListener('play', function(e) {
              var parent = $(this).closest('.audio-player');
              var playButton = parent.find('.playpause');

              $(this).removeClass('is-paused').addClass('is-playing');
              playButton.find('#play-btn').attr("src","static/images/audiojs/pause.svg")
              parent.removeClass('is-paused').addClass('is-playing');
          });

          mediaElement.addEventListener('pause', function(e) {
              var parent = $(this).closest('.audio-player');
              var playButton = parent.find('.playpause');
              playButton.removeClass('is-playing').addClass('is-paused');
              playButton.find('#play-btn').attr("src","static/images/audiojs/play.svg")
              parent.removeClass('is-playing').addClass('is-paused');
          });
      },
      error: function(mediaElement) {
          // Handle error
      }
  });

  $('.audio-player').on('click', function(event) {
    var target = $(event.target);
    if (!target.hasClass('playpause')) {
        var audioPlayer = $(this);
        var mediaElement = audioPlayer.find('audio')[0];
        var boundingRect = audioPlayer[0].getBoundingClientRect();
        var offsetX = event.clientX - boundingRect.left;
        var percentage = offsetX / boundingRect.width;
        console.log(percentage)
        var duration = mediaElement.duration;
        percentage -= 0.092;
        var seekTime = (percentage * duration);
        // Ensure seekTime is within valid range
        if (isFinite(seekTime) && seekTime >= 0 && seekTime <= duration) {
            mediaElement.currentTime = seekTime;
        }
    }
});
}

// Initialize MediaElementPlayer on document ready
$(document).ready(function() {
  initializeMediaElements();
});
