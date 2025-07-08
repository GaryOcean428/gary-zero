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

  // Use a dedicated initialization flag to determine if the UI needs to be built
  if (!window.__uiInitialized) {
    const buildUI = () => {
      if (!window.__uiInitialized) {
        window.UIStructureBuilder?.buildCompleteInterface();
        window.__uiInitialized = true;
      }
    };

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', buildUI);
    } else {
      buildUI();
    }
  }
})();
