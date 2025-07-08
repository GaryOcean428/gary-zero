import './ui/ui-structure-builder.js';
import './ui/integrate-ui-fix.js';

console.log('✅ UI restoration modules loaded');

window.verifyUI = function () {
  const elements = {
    'right-panel': 'Main chat container',
    'chat-history': 'Message display area',
    'chat-input': 'Text input field',
    'send-button': 'Send button',
    'status-section': 'Status bar',
    'progress-bar': 'Progress indicator',
    'auto-scroll-switch': 'Auto-scroll toggle',
  };

  console.log('🔍 UI Element Verification:');
  Object.entries(elements).forEach(([id, description]) => {
    const el = document.getElementById(id);
    console.log(`${el ? '✅' : '❌'} #${id} - ${description}`);
  });
};
