const cards = document.querySelectorAll('.draggable-card');
let draggedElement = null;
// Explicitly scope reordering to the cards list container
const cardsContainer = document.getElementById('cards-list');

function bindCardDragHandlers(card) {
  let dragAllowed = false;

  // Decide if a drag is allowed based on where pointer down occurred
  card.addEventListener('pointerdown', function(e) {
    const inModal = e.target && e.target.closest('.modal');
    const inCardBody = e.target && e.target.closest('.card');
    dragAllowed = !!inCardBody && !inModal;
  });

  card.addEventListener('pointerup', function() {
    dragAllowed = false;
  });

  // Drag start
  card.addEventListener('dragstart', function(e) {
    // Only allow starting a drag if pointer originated inside card body and not in modal
    if (!dragAllowed) {
      e.preventDefault();
      return;
    }
    dragAllowed = false;
    draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
  });

  // Drag end
  card.addEventListener('dragend', function(e) {
    this.classList.remove('dragging');
    document.querySelectorAll('.draggable-card').forEach(c => c.classList.remove('drag-over'));
    draggedElement = null;
  });

  // Drag over
  card.addEventListener('dragover', function(e) {
    if (e.preventDefault) {
      e.preventDefault();
    }

    // Don't allow dropping on non-draggable cards
    if (!this.classList.contains('draggable-card')) {
      e.dataTransfer.dropEffect = 'none';
      return false;
    }

    // If no dragged element (e.g., newly added card without handlers), do nothing
    if (!draggedElement) {
      e.dataTransfer.dropEffect = 'none';
      return false;
    }

    e.dataTransfer.dropEffect = 'move';

    // Always insert within the explicit cards container (fallback to parent if missing)
    const targetContainer = cardsContainer || this.parentElement;
    const afterElement = getDragAfterElement(targetContainer, e.clientY);
    if (afterElement == null) {
      targetContainer.appendChild(draggedElement);
    } else {
      targetContainer.insertBefore(draggedElement, afterElement);
    }

    return false;
  });

  // Drag enter
  card.addEventListener('dragenter', function(e) {
    if (this !== draggedElement) {
      this.classList.add('drag-over');
    }
  });

  // Drag leave
  card.addEventListener('dragleave', function(e) {
    this.classList.remove('drag-over');
  });

  // Drop
  card.addEventListener('drop', function(e) {
    if (e.stopPropagation) {
      e.stopPropagation();
    }
    this.classList.remove('drag-over');

    // Optional: Save the new order to the backend
    saveCardOrder();

    return false;
  });
}

// Bind existing cards on load
document.querySelectorAll('.draggable-card').forEach(bindCardDragHandlers);
// Expose binder for clones
window.bindCardDragHandlers = bindCardDragHandlers;

function getDragAfterElement(container, y) {
  const draggableElements = [...container.querySelectorAll('.draggable-card:not(.dragging)')];

  return draggableElements.reduce((closest, child) => {
    const box = child.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;

    if (offset < 0 && offset > closest.offset) {
      return { offset: offset, element: child };
    } else {
      return closest;
    }
  }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function saveCardOrder() {
  // Collect the new order of cards including the non-draggable first card
  // We take the DOM order of all module cards inside #cards-list
  const orderedIds = Array.from(document.querySelectorAll('#cards-list > .collectableCard'))
    .map(card => card.dataset.instanceId || card.dataset.cardId);

  // Reflect current order in hidden field so POST includes it
  const hidden = document.getElementById('module_order');
  if (hidden) hidden.value = JSON.stringify(orderedIds);

  console.log('New card order (instanceIds):', orderedIds);

}

// Initialize the hidden field with the current order on first load
saveCardOrder();


function deleteCard(buttonObject) {
  parentModal = buttonObject.closest('.modal');
  modalInstance = bootstrap.Modal.getInstance(parentModal);
  modalInstance.hide();

  parentDiv = buttonObject.closest('.collectableCard');
  parentDiv.remove();
  saveCardOrder();
  resetAllCardNumbering();
}
