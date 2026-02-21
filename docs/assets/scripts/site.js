(function () {
  function applyTheme() {
    var root = document.documentElement;
    var select = document.getElementById("theme-select");
    var saved = localStorage.getItem("tutr-docs-theme") || "dark";

    root.setAttribute("data-theme", saved);

    if (select) {
      select.value = saved;
      select.addEventListener("change", function (event) {
        var next = event.target.value;
        root.setAttribute("data-theme", next);
        localStorage.setItem("tutr-docs-theme", next);
      });
    }
  }

  function fallbackCopy(text) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "absolute";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    var copied = false;
    try {
      copied = document.execCommand("copy");
    } catch (_error) {
      copied = false;
    }
    document.body.removeChild(textarea);
    return copied;
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(
        function () {
          return true;
        },
        function () {
          return fallbackCopy(text);
        }
      );
    }
    return Promise.resolve(fallbackCopy(text));
  }

  function addCopyButtons() {
    var blocks = document.querySelectorAll("pre");
    blocks.forEach(function (block) {
      var code = block.querySelector("code");
      if (!code) {
        return;
      }

      var text = code.textContent || "";
      if (!text.trim()) {
        return;
      }

      var button = document.createElement("button");
      button.type = "button";
      button.className = "copy-btn";
      button.textContent = "Copy";
      button.setAttribute("aria-label", "Copy code to clipboard");

      button.addEventListener("click", function () {
        copyText(text).then(function (ok) {
          button.textContent = ok ? "Copied" : "Failed";
          button.classList.toggle("copied", ok);
          window.setTimeout(function () {
            button.textContent = "Copy";
            button.classList.remove("copied");
          }, 1400);
        });
      });

      block.appendChild(button);
    });
  }

  applyTheme();
  addCopyButtons();
})();
