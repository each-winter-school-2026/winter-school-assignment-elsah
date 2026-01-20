const cardListDiv = document.getElementById('cards-list');

const addModuleModal = document.getElementById('addModuleModal');
if (addModuleModal) {
    addModuleModal.addEventListener('hidden.bs.modal', () => {
        unselectAllCards();
    });
}

function genInstanceId() {
    return 'inst_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function uniquifyIdsWithin(root) {
    const unique = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    const elementsWithId = Array.from(root.querySelectorAll('[id]'));
    const idMap = new Map();
    elementsWithId.forEach(el => {
        const oldId = el.id;
        const newId = `${oldId}__${unique}`;
        idMap.set(oldId, newId);
    });

    const refAttrs = ['data-bs-target', 'aria-labelledby', 'aria-controls', 'for', 'href'];
    refAttrs.forEach(attr => {
        root.querySelectorAll(`[${attr}]`).forEach(el => {
            let val = el.getAttribute(attr);
            if (!val) return;
            idMap.forEach((newId, oldId) => {
                val = val.replace(new RegExp(`#${oldId}\\b`, 'g'), `#${newId}`);
                val = val.replace(new RegExp(`\\b${oldId}\\b`, 'g'), newId);
            });
            el.setAttribute(attr, val);
        });
    });

    elementsWithId.forEach(el => { el.id = idMap.get(el.id); });
}

function retagCardNames(root) {
    const instanceId = root.dataset.instanceId || root.dataset.cardId;
    if (!instanceId) return;

    // Prefix all non-hidden controls with instanceId:
    root.querySelectorAll('input:not([type="hidden"]), select, textarea').forEach(ctrl => {
        const name = ctrl.getAttribute('name');
        if (!name) return;
        const base = name.includes(':') ? name.split(':', 2)[1] : name;
        ctrl.setAttribute('name', `${instanceId}:${base}`);
    });

    // Ensure we carry module type for this instance
    let mt = root.querySelector('input[type="hidden"][name^="ModuleType:"]');
    if (!mt) {
        mt = document.createElement('input');
        mt.type = 'hidden';
        root.appendChild(mt);
    }
    mt.name = `ModuleType:${instanceId}`;
    mt.value = root.dataset.moduleType || root.dataset.cardId || '';

    // Keep Field: inputs as-is (modal.js relies on them) - don't retag
}

function selectCurrentCard(cardElement) {
    console.log("Card selected:", cardElement);
    unselectAllCards();
    // Add 'selected-card' class to the currently selected card
    cardElement.querySelector('.card').classList.add('selected-card');
}

function unselectAllCards() {
    document.querySelectorAll('.collectableCard').forEach(function(el) {
        el.querySelector('.card').classList.remove('selected-card');
    });
}

function insertCard() {
    const selected = document.querySelector('.selected-card');
    if (!selected) return;
    selected.classList.remove('selected-card');

    const cardClone = selected.parentElement.cloneNode(true);

    // Make it a real draggable module card
    cardClone.classList.add('draggable-card');
    cardClone.setAttribute('draggable', 'true');
    cardClone.removeAttribute('onclick');

    // New instance id
    const newInstanceId = genInstanceId();
    cardClone.dataset.instanceId = newInstanceId;

    // Ensure module type is present on wrapper
    if (!cardClone.dataset.moduleType) {
        cardClone.dataset.moduleType = cardClone.dataset.cardId || '';
    }

    // Enable settings button within the clone
    const settingsBtn = cardClone.querySelector('#settingsButton') || cardClone.querySelector('[id="settingsButton"]');
    if (settingsBtn) {
        settingsBtn.removeAttribute('disabled');
        settingsBtn.removeAttribute('aria-disabled');
        settingsBtn.classList.remove('invisible');
    }



    // Update title with instance number
    addVisualCardIterator(cardClone);

    // Uniquify DOM ids inside clone (modals/buttons)
    uniquifyIdsWithin(cardClone);

    // Prefix field names with instanceId and add ModuleType:hidden
    retagCardNames(cardClone);

    // Append, bind DnD, persist order
    cardListDiv.appendChild(cardClone);
    if (window.bindCardDragHandlers) window.bindCardDragHandlers(cardClone);
    if (typeof saveCardOrder === 'function') saveCardOrder();

    // Initialize the settings modal for this cloned card
    const newModal = cardClone.querySelector('.modal[id*="_settingsModal"]');
    console.log(window.initializeSettingsModal)
    console.log("New modal found:", newModal);
    console.log(newModal && window.initializeSettingsModal)
    if (newModal && window.initializeSettingsModal) {
        window.initializeSettingsModal(newModal);
    }
    disableEnterKeySubmission();
}

function addVisualCardIterator(cardElement) {
    // Count existing instances of this module type to number it
    const moduleType = cardElement.dataset.moduleType;
    const titleEl = cardElement.querySelector('.card-title');
    if (!titleEl) return;

    const originalText = titleEl.textContent.trim();
    const cleanText = originalText.includes(' - #') ? originalText.split(' - #')[0] : originalText;

    // Count all cards of this type that already have a number
    const existingCount = Array.from(cardListDiv.querySelectorAll('.collectableCard')).filter(card => {
        if (card.dataset.moduleType !== moduleType) return false;
        const title = card.querySelector('.card-title');
        return title && title.textContent.includes(' - #');
    }).length;

    const instanceNumber = existingCount + 1;
    titleEl.innerHTML = `<b>${cleanText}</b> - #${instanceNumber}`;
}

function resetAllCardNumbering() {
    const moduleTypeMap = new Map();
    
    document.querySelectorAll('#cards-list > .collectableCard').forEach(cardElement => {
        const moduleType = cardElement.dataset.moduleType;
        const titleEl = cardElement.querySelector('.card-title');
        if (!titleEl) return;

        const originalText = titleEl.textContent.trim();
        const cleanText = originalText.includes(' - #') ? originalText.split(' - #')[0] : originalText;

        const count = (moduleTypeMap.get(moduleType) || 0) + 1;
        moduleTypeMap.set(moduleType, count);

        titleEl.innerHTML = `<b>${cleanText}</b> - #${count}`;
    });
}

function disableEnterKeySubmission() {
    document.querySelectorAll('input')
        .forEach(input => {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                }
            });
        });
}


// Init existing cards on first load: ensure instanceId and prefix names
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('#cards-list > .collectableCard').forEach(root => {
        if (!root.dataset.instanceId) {
            root.dataset.instanceId = root.dataset.cardId || genInstanceId();
        }
        // also ensure moduleType metadata is set
        if (!root.dataset.moduleType) {
            root.dataset.moduleType = root.dataset.cardId || '';
        }
        retagCardNames(root);
    });
});

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('#cards-list > .collectableCard').forEach(cardElement => {
        addVisualCardIterator(cardElement);
    });
});