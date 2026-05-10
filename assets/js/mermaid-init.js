// Mermaid initialization for GitHub Pages
(function() {
  'use strict';
  
  function initMermaid() {
    if (typeof mermaid === 'undefined') {
      console.log('Mermaid not loaded yet, retrying...');
      setTimeout(initMermaid, 100);
      return;
    }

    console.log('Initializing Mermaid...');
    
    mermaid.initialize({ 
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
      themeVariables: {
        darkMode: false,
        background: '#ffffff',
        primaryColor: '#fff',
        primaryTextColor: '#000',
        primaryBorderColor: '#333',
        lineColor: '#333',
        secondaryColor: '#f4f4f4',
        tertiaryColor: '#fff'
      }
    });

    function convertMermaidBlocks() {
      console.log('Converting Mermaid blocks...');
      const codeBlocks = document.querySelectorAll('pre > code.language-mermaid');
      console.log('Found ' + codeBlocks.length + ' mermaid code blocks');
      
      codeBlocks.forEach((codeBlock) => {
        if (codeBlock.getAttribute('data-mermaid-processed')) {
          return;
        }
        
        const mermaidDiv = document.createElement('div');
        mermaidDiv.className = 'mermaid';
        mermaidDiv.textContent = codeBlock.textContent;
        
        const preBlock = codeBlock.parentElement;
        preBlock.parentElement.replaceChild(mermaidDiv, preBlock);
        codeBlock.setAttribute('data-mermaid-processed', 'true');
      });
      
      mermaid.init(undefined, document.querySelectorAll('.mermaid:not([data-processed="true"])'));
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', convertMermaidBlocks);
    } else {
      convertMermaidBlocks();
    }

    // Handle Hydejack push-state navigation
    if (document.getElementById('_pushState')) {
      document.getElementById('_pushState').addEventListener('hy-push-state-load', function() {
        setTimeout(convertMermaidBlocks, 100);
      });
    }
  }

  initMermaid();
})();
