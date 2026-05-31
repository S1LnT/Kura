let page = 1; // Assuming page 1 is already loaded
var postID = 0;
var load_trigger = document.getElementById("load_trigger");
var text = load_trigger.getAttribute("data-text");

function copyToClip(id) {
  // Get the text field
  var copyText = document.getElementById(id);

  // Select the text field
  var textToCopy = copyText.textContent;

  // Use the Clipboard API if available
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard
      .writeText(textToCopy)
      .then(function () {
        console.log("Text copied to clipboard");
      })
      .catch(function (err) {
        console.error("Failed to copy text: ", err);
      });
  } else {
    // Fallback method for older browsers
    var textArea = document.createElement("textarea");
    textArea.value = textToCopy;

    // Avoid scrolling to bottom
    textArea.style.position = "fixed";
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.width = "2em";
    textArea.style.height = "2em";
    textArea.style.padding = "0";
    textArea.style.border = "none";
    textArea.style.outline = "none";
    textArea.style.boxShadow = "none";
    textArea.style.background = "transparent";

    document.body.appendChild(textArea);
    textArea.select();

    try {
      var successful = document.execCommand("copy");
      var msg = successful ? "successful" : "unsuccessful";
      console.log("Fallback: Copying text command was " + msg);
    } catch (err) {
      console.error("Fallback: Oops, unable to copy", err);
    }

    document.body.removeChild(textArea);
  }
}

function copyLink(id) {
  var fid = "form-" + id;
  var form = document.getElementById(fid);
  var link = form.action;
  navigator.clipboard.writeText(link);
}

function loadMorePosts(searchValue) {
  const url = searchValue
    ? `/load_posts?page=${page}&search=${searchValue}&searchText=${text}`
    : `/load_posts?page=${page}`;
  fetch(url)
    .then((response) => response.json())
    .then((posts) => {
      if (posts.length > 0) {
        console.log(posts.length);
        // Using a for loop starting from index 0
        for (let i of posts.length) {
          postID++;
          const post = posts[i];
          const user_perm = post.permissions;
          const current_user = post.current_user;
          if (JSON.parse(post.saved_by).includes(current_user)) {
            
            var saved_icon = '<img src=static/images/buttons/bm-rm.svg style ="width:100%;height:100%;filter: invert(0%) brightness(100%) contrast(100%);" />';
          
          } else {
            var saved_icon = '<img src=static/images/buttons/bm-add.svg style ="width:100%;height:100%;filter: invert(0%) brightness(100%) contrast(100%);" />';
          }
          // Assuming your HTML structure is similar to before
          const postHTML = /*html*/ `
            <div class="animated fadeIn card" style="box-shadow:none;" >
              <div class="custom-header">
                <div class="top" id="title"><span><strong>${
                  post.title
                }</strong></span></div>
                <div class="userDeatils" id="author"><span style="font-style: italic; font-size:smaller; color:gray;">by: ${
                  post.author
                } on: ${post.date_created}</span></div>
              </div>
              
              <div style="padding: 20px;">
                <!-- Adjust this part based on the file type of the post -->
                ${
                  post.file_type === "video"
                    ? /*html*/ `
              ${post.desc}
              <br /><br />
                  <div>
                    <video
                      id="my-video"
                      class="video-js"
                      controls
                      preload="auto"
                      data-setup="{}"
                      style="width: 100%; height:20vh;"
                    >
                      <source src="/fileserve/${post.file_name}" type='video/webm' />
                      <p class="vjs-no-js">
                        To view this video please enable JavaScript, and consider upgrading to a
                        web browser that
                        <a href="https://videojs.com/html5-video-support/" target="_blank">supports HTML5 video</a>
                      </p>
                    </video>
                    <div style="font-style: italic; font-size:x-small; color:gray;">${post.file_name}</div>
                  </div>
                  <br>
                <div>
                <form method="" action="/download/${post.file_name}" id="form-${postID}">
 
                <button type="submit"  class="btn dl"   style="background-color:#feaae4; border:10; box-shadow:none; border-color:black;"><img src=static/images/buttons/download.svg style ="width:3%;height:3%;filter: invert(0%) brightness(100%) contrast(100%);" /></button>

    </form></div>
                `
                    : post.file_type === "audio"
                    ? /*html*/ `
                ${post.desc}
                <br /><br />
                  <div class="row" style="width: 104.3%;">
                    <br /><br /><br />
                    <div class="col-md-4 col-md-offset-4" style="width: 92%;">
                      <div class="panel panel-default audio-player is-paused">
                      <button style="position:absolute; z-index:998; top:0%; left:0%;"class=" playpause is-paused" disabled><img id="play-btn" src=static/images/audiojs/play.svg style="filter: invert(100%) brightness(100%) contrast(100%);width: 37px; height: 50px; position: relative; left: -3px; transform: translate(0px, -6px); top: 1.3px;"/></button>
                        <div class="song-info">
                          <span class="song-title">${post.file_name}</span><br />
                          <audio controls>
                            <source src="/fileserve/${post.file_name}" type="audio/mpeg">
                            Your browser does not support the audio element.
                          </audio>
                          <span class="song-time"><span class="song-current-time"></span><span class="song-duration"></span></span>
                        </div>
                        <div class="progress" style="transform: translate(48px, 0px)">
                          <div class="progress-bar progress-bar-success" role="progressbar">&nbsp;</div>
                        </div>
                      </div>
                    </div>
                    
                  </div>
                 <div>
                <form method="" action="/download/${post.file_name}" id="form-${postID}">
 
                <button type="submit"  class="btn dl"   style="background-color:#feaae4; transition: background-color 0.3s ease; border:10; box-shadow:none; border-color:black;"><img src=static/images/buttons/download.svg style ="width:3%;height:3%;filter: invert(0%) brightness(100%) contrast(100%);" /></button>

    </form></div>
                `
                    : post.file_type === "text"
                    ? /*html*/ `
                <div>
                  <p id=${postID}>${post.desc}</p>
                  </div>

                <br>
                <div>
                <button type="submit" class="btn"onclick="copyToClip(${postID})" style="background-color:#feaae4; border:10; box-shadow:none; border-color:black; color:black; width:100%;">Copy text</button>
                </div>
                `
                    : post.file_type === "image"
                    ? /*html*/ `
                <div>
                 ${post.desc}\
                  <br><br>
                  <img src="/fileserve/${post.file_name}" style="width:auto; height:auto; max-width:100%; max-height:20vh;"/>
                  </div>

                <br>
                <div>
                <form method="" action="/download/${post.file_name}">
 
                <button type="submit"  class="btn dl"   style="background-color:#feaae4; border:10; box-shadow:none; border-color:black;"><img src=static/images/buttons/download.svg style ="width:3%;height:3%;filter: invert(0%) brightness(100%) contrast(100%);" /></button>

          </form></div>
                `
                    : /*html*/ `
              <div>
                  <p id=${postID}>${post.desc}</p>
                  </div>
                <span style="font-weight:700; text-overflow: ellipsis;white-space: nowrap;overflow: hidden; display: inline-block; max-width: 100%;">FILE : ${post.file_name}</span>
                <br>
                <br>
                 <div style="display: flex; width: 100%; justify-content: space-between;">
                <form method="" action="/download/${post.file_name}" id="form-${postID}" style="display: inline-block;  max-width:25%; width :25%; max-height:38px">
 
                <button type="submit"  class="btn" style="background-color:#feaae4; border:10; box-shadow:none; border-color:black; width :100%;"><img src=static/images/buttons/download.svg style ="width:25%;height:3%;filter: invert(0%) brightness(100%) contrast(100%);" /></button>
                </form>
    
    <button onclick="copyLink(${postID})" class="btn" style="background-color:#feaae4; border:10; box-shadow:none; border-color:black; width :25%; max-width:25%; display: inline-block; max-height:38px"><img src=static/images/buttons/copy.svg style ="width:100%;height:100%;" /></button>
    <form action="" method="post" style="display: inline-block;  max-width:25%; width :25%; max-height:38px">
    <button type="submit" class="btn" style="background-color:#feaae4; border:10; box-shadow:none; border-color:black;width :100%;">${saved_icon}</button>  
    </form>
     <form  method="post" action="/pin/${post.id}" style="display: inline-block; width :25%; max-width:25%; max-height:38px">
    <button type="submit" class="btn" style="background-color:#feaae4; border:10; box-shadow:none; border-color:black; width :100%;">pin</button>
    </form>       

  </div>
                `
                }               
</div>  
              </div>
              
            </div>
            <br>
          `;
          if (post.lowest_view_perm <= user_perm) {
            document
              .querySelector("#scroller")
              .insertAdjacentHTML("beforeend", postHTML);
          }
        }
        // Initialize MediaElementPlayer for new elements
        initializeMediaElements();
        page++;
      } else {
        console.log("No more posts to load");
        load_trigger.remove();
      }
    })
    .catch((error) => {
      console.error("Error fetching more posts:", error);
    });
  console.log(searchValue);
}

var observer = new IntersectionObserver((entries) => {
  if (entries[0].intersectionRatio <= 0) {
    return;
  }
  loadMorePosts(load_trigger.getAttribute("data-search"));
});
observer.observe(load_trigger);
