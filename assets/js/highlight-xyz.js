(function () {
  'use strict';

  var QUOTED_TEXT_REGEX = /(^|[\s([\{>])(?:'([^'\n]+)'|‘([^’\n]+)’)(?=$|[\s)\]}<.,!?;:])/g;
  var SKIP_TAGS = {
    SCRIPT: true,
    STYLE: true,
    PRE: true,
    CODE: true,
    KBD: true,
    SAMP: true,
    TEXTAREA: true,
    NOSCRIPT: true,
    SVG: true,
    MATH: true
  };

  function shouldSkipNode(node) {
    if (!node || !node.parentElement) {
      return true;
    }

    var parent = node.parentElement;
    if (SKIP_TAGS[parent.tagName]) {
      return true;
    }

    if (parent.closest('pre, code, kbd, samp, script, style, textarea, noscript, svg, math')) {
      return true;
    }

    if (parent.closest('.quoted-highlight')) {
      return true;
    }

    return false;
  }

  function wrapTextNode(textNode) {
    var text = textNode.nodeValue;
    if (!text) {
      return;
    }

    QUOTED_TEXT_REGEX.lastIndex = 0;
    if (!QUOTED_TEXT_REGEX.test(text)) {
      return;
    }

    var fragment = document.createDocumentFragment();
    var lastIndex = 0;

    QUOTED_TEXT_REGEX.lastIndex = 0;
    var match = QUOTED_TEXT_REGEX.exec(text);
    while (match) {
      var prefix = match[1] || '';
      var quoted;
      if (match[2]) {
        quoted = "'" + match[2] + "'";
      } else {
        quoted = '‘' + match[3] + '’';
      }
      var start = match.index + prefix.length;
      var end = start + quoted.length;

      if (start > lastIndex) {
        fragment.appendChild(document.createTextNode(text.slice(lastIndex, start)));
      }

      var span = document.createElement('span');
      span.className = 'quoted-highlight';
      span.textContent = quoted;
      fragment.appendChild(span);

      lastIndex = end;
      match = QUOTED_TEXT_REGEX.exec(text);
    }

    if (lastIndex < text.length) {
      fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
    }

    textNode.parentNode.replaceChild(fragment, textNode);
  }

  function highlightIn(root) {
    if (!root) {
      return;
    }

    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    var nodes = [];
    var current = walker.nextNode();

    while (current) {
      if (!shouldSkipNode(current)) {
        nodes.push(current);
      }
      current = walker.nextNode();
    }

    for (var i = 0; i < nodes.length; i += 1) {
      wrapTextNode(nodes[i]);
    }

    // Markdown inline code (`...`) is rendered as <code>, not plain text with backticks.
    var inlineCode = root.querySelectorAll('code');
    for (var j = 0; j < inlineCode.length; j += 1) {
      if (!inlineCode[j].closest('pre')) {
        inlineCode[j].classList.add('quoted-highlight');
      }
    }
  }

  function runHighlight() {
    var postContentRoots = document.querySelectorAll('article.page.post');
    for (var i = 0; i < postContentRoots.length; i += 1) {
      highlightIn(postContentRoots[i]);
    }
  }

  document.addEventListener('DOMContentLoaded', runHighlight);

  var pushStateEl = document.getElementById('_pushState');
  if (pushStateEl && !window._noPushState) {
    pushStateEl.addEventListener('hy-push-state-load', runHighlight);
    pushStateEl.addEventListener('hy-push-state-ready', runHighlight);
  }
})();
