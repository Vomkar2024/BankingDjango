/**
 * OMOM Bank - Core Interactive UI Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  initModals();
  initDropdowns();
  initThemeToggle();
  initClipboard();
  initBeneficiarySelector();
  initBillPresets();
  initAutoDismissAlerts();
});

// 1. Modals Control
function initModals() {
  // Modal Triggers
  document.querySelectorAll('[data-open-modal]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const modalId = trigger.getAttribute('data-open-modal');
      openModal(modalId);
    });
  });

  // Modal Closers
  document.querySelectorAll('[data-close-modal]').forEach(closer => {
    closer.addEventListener('click', (e) => {
      e.preventDefault();
      const modal = closer.closest('.modal-backdrop');
      if (modal) {
        modal.classList.remove('active');
      }
    });
  });

  // Backdrop click closes modal
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove('active');
      }
    });
  });

  // ESC key closes any open modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.active').forEach(modal => {
        modal.classList.remove('active');
      });
      closeAllDropdowns();
    }
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    const firstInput = modal.querySelector('input:not([type="hidden"]), select');
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 100);
    }
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

// 2. Dropdown Menus (User Profile, Notifications)
function initDropdowns() {
  document.querySelectorAll('[data-dropdown-toggle]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const targetId = btn.getAttribute('data-dropdown-toggle');
      const targetMenu = document.getElementById(targetId);

      // Close others first
      document.querySelectorAll('.dropdown-menu-custom').forEach(menu => {
        if (menu !== targetMenu) {
          menu.classList.remove('show');
        }
      });

      if (targetMenu) {
        targetMenu.classList.toggle('show');
      }
    });
  });

  document.addEventListener('click', (e) => {
    closeAllDropdowns();
  });
}

function closeAllDropdowns() {
  document.querySelectorAll('.dropdown-menu-custom').forEach(menu => {
    menu.classList.remove('show');
  });
}

// 3. Theme Toggle (Dark / Light)
function initThemeToggle() {
  const currentTheme = localStorage.getItem('omom_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', currentTheme);

  document.querySelectorAll('[data-toggle-theme]').forEach(btn => {
    btn.addEventListener('click', () => {
      const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('omom_theme', theme);
    });
  });
}

// 4. Clipboard helper
function initClipboard() {
  document.querySelectorAll('[data-copy]').forEach(el => {
    el.addEventListener('click', () => {
      const text = el.getAttribute('data-copy');
      navigator.clipboard.writeText(text).then(() => {
        const originalText = el.innerText;
        el.innerText = 'Copied!';
        setTimeout(() => {
          el.innerText = originalText;
        }, 1800);
      });
    });
  });
}

// 5. Beneficiary Selector Quick Autofill
function initBeneficiarySelector() {
  const select = document.getElementById('beneficiarySelect');
  const targetInput = document.getElementById('transferTargetAccount');
  const recipientInput = document.getElementById('transferRecipientName');

  if (select && targetInput && recipientInput) {
    select.addEventListener('change', () => {
      const option = select.options[select.selectedIndex];
      if (option && option.value) {
        const acc = option.getAttribute('data-account');
        const name = option.getAttribute('data-name');
        if (acc) targetInput.value = acc;
        if (name) recipientInput.value = name;
      }
    });
  }
}

// 6. Bill Presets Auto Fill
function initBillPresets() {
  const billType = document.getElementById('billTypeSelect');
  const billerName = document.getElementById('billerNameInput');
  const amountInput = document.getElementById('billAmountInput');

  if (billType && billerName) {
    billType.addEventListener('change', () => {
      const val = billType.value;
      if (val === 'Electricity') {
        billerName.value = 'Adani Electricity Mumbai';
        if (amountInput) amountInput.value = '1250';
      } else if (val === 'Broadband') {
        billerName.value = 'Jio Fiber High Speed';
        if (amountInput) amountInput.value = '999';
      } else if (val === 'Mobile') {
        billerName.value = 'Airtel Postpaid';
        if (amountInput) amountInput.value = '749';
      } else if (val === 'Water') {
        billerName.value = 'Municipal Corporation Water Board';
        if (amountInput) amountInput.value = '450';
      } else if (val === 'Gas') {
        billerName.value = 'Mahanagar Gas Limited';
        if (amountInput) amountInput.value = '820';
      }
    });
  }
}

// 7. Auto-dismiss alerts
function initAutoDismissAlerts() {
  document.querySelectorAll('.alert-custom').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      alert.style.transition = 'all 0.4s ease';
      setTimeout(() => alert.remove(), 400);
    }, 6000);
  });
}

// Quick Demo Login helper
function fillDemoCredentials(username, password) {
  const userField = document.getElementById('id_username');
  const passField = document.getElementById('id_password');
  if (userField && passField) {
    userField.value = username;
    passField.value = password;
    userField.classList.add('highlight-glow');
    passField.classList.add('highlight-glow');
    setTimeout(() => {
      userField.form.submit();
    }, 250);
  }
}
