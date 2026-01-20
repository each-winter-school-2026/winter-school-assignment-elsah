// Initialize a single settings modal so dynamically added modals work too
function initializeSettingsModal(modalEl) {
  console.log("Initializing settings modal:", modalEl);
  if (!modalEl || modalEl.__ewoksModalInitialized) return;
  modalEl.__ewoksModalInitialized = true;

  let snapshot = [];
  let saved = false;

  // Take a snapshot of values on open
  const onShow = () => {
    const fields = modalEl.querySelectorAll('input, select, textarea');
    snapshot = Array.from(fields).map(el => ({
      el,
      tag: el.tagName,
      type: el.type,
      value: (el.type === 'checkbox' || el.type === 'radio') ? el.checked : el.value
    }));
    saved = false;
  };

  // Handle Enter key press to trigger save
  const onKeyDown = (e) => {
    if (e.key === 'Enter' && modalEl.classList.contains('show')) {
      const saveButton = modalEl.querySelector('[data-role="modal-save"]');
      if (saveButton) {
        e.preventDefault();
        saveButton.click();
      }
    }
  };

  // Use event delegation for the Save button (works after cloning)
  const onClick = (e) => {
    const target = e.target;
    if (target && target.matches('[data-role="modal-save"]')) {
      // Validate all form fields in the modal
      const modalFields = modalEl.querySelectorAll('input, select, textarea');
      let isValid = true;
      
      // Trigger validation on each field
      modalFields.forEach(field => {
        if (!field.checkValidity()) {
          isValid = false;
          field.classList.add('is-invalid');
          field.reportValidity(); // Shows the browser's native validation message
          return;
        } else {
          field.classList.remove('is-invalid');
        }
      });
      
      // Only close modal if all fields are valid
      if (isValid) {
        saved = true;
        const instance = bootstrap.Modal.getOrCreateInstance(modalEl);
        instance.hide();
      }
    }
  };

  // Restore snapshot if closed without saving
  const onHidden = () => {
    if (!saved && snapshot.length) {
      snapshot.forEach(s => {
        if (s.type === 'checkbox' || s.type === 'radio') {
          s.el.checked = s.value;
        } else if (s.type === 'file') {
          if (!s.value) s.el.value = '';
        } else {
          s.el.value = s.value;
        }
        s.el.dispatchEvent(new Event('input', { bubbles: true }));
        s.el.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }
    snapshot = [];
    saved = false;
  };

  modalEl.addEventListener('show.bs.modal', onShow);
  modalEl.addEventListener('click', onClick);
  modalEl.addEventListener('keydown', onKeyDown);
  modalEl.addEventListener('hidden.bs.modal', onHidden);
}

// Expose initializer for dynamically inserted cards
window.initializeSettingsModal = initializeSettingsModal;

// Initialize all existing modals on first load
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.modal[id$="_settingsModal"]').forEach(initializeSettingsModal);
});