(function () {
  const originalInit = window.initializeApp;
  window.initializeApp = function (...args) {
    if (window.UIStructureBuilder) {
      window.UIStructureBuilder.buildCompleteInterface();
    }
    if (originalInit) {
      return originalInit.apply(this, args);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      if (!document.getElementById('right-panel')) {
        window.UIStructureBuilder?.buildCompleteInterface();
      }
    });
  } else if (!document.getElementById('right-panel')) {
    window.UIStructureBuilder?.buildCompleteInterface();
  }
})();
