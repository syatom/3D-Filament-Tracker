// Custom JavaScript for Spool Tracker

// ========================================
// DARK MODE FUNCTIONALITY
// ========================================

/**
 * Update dark mode icon and text based on current state
 * @param {boolean} isDarkMode - Current dark mode state
 */
function updateDarkModeIcon(isDarkMode) {
  const icon = document.getElementById("darkModeIcon");
  const text = document.getElementById("darkModeText");

  if (icon && text) {
    if (isDarkMode) {
      icon.className = "bi bi-sun-fill";
      text.textContent = "Light Mode";
    } else {
      icon.className = "bi bi-moon-fill";
      text.textContent = "Dark Mode";
    }
  }
}

/**
 * Toggle dark mode theme
 */
function toggleDarkMode() {
  const htmlElement = document.documentElement;
  const currentTheme = htmlElement.getAttribute("data-bs-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  const isDarkMode = newTheme === "dark";

  // Apply theme immediately for instant feedback
  htmlElement.setAttribute("data-bs-theme", newTheme);
  updateDarkModeIcon(isDarkMode);

  // Save preference to server
  fetch("/auth/toggle-dark-mode", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    credentials: "same-origin",
  })
    .then((response) => {
      if (!response.ok) {
        console.error("Server error:", response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (!data.success) {
        console.error("Failed to save dark mode preference:", data.error);
        // Revert the change
        htmlElement.setAttribute("data-bs-theme", currentTheme);
        updateDarkModeIcon(currentTheme === "dark");
      }
    })
    .catch((error) => {
      console.error("Error toggling dark mode:", error);
      // Revert the visual change if save fails
      htmlElement.setAttribute("data-bs-theme", currentTheme);
      updateDarkModeIcon(currentTheme === "dark");
    });
}

/**
 * Get CSRF token from meta tag or cookie
 * @returns {string} CSRF token
 */
function getCsrfToken() {
  // Try to get from meta tag first
  const metaToken = document.querySelector('meta[name="csrf-token"]');
  if (metaToken) {
    return metaToken.getAttribute("content");
  }

  // Fallback to cookie
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split("=");
    if (name === "csrf_token") {
      return decodeURIComponent(value);
    }
  }

  return "";
}

// Initialize dark mode toggle on page load
document.addEventListener("DOMContentLoaded", function () {
  const darkModeToggle = document.getElementById("darkModeToggle");

  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", function (e) {
      e.preventDefault();
      toggleDarkMode();
    });
  }

  // Initialize delete usage modal if it exists
  initializeDeleteUsageModal();
});

// ========================================
// DELETE USAGE FUNCTIONALITY
// ========================================

/**
 * Initialize delete usage modal and handlers
 */
function initializeDeleteUsageModal() {
  const deleteModal = document.getElementById("deleteUsageModal");
  
  if (!deleteModal) {
    return; // Modal doesn't exist on this page
  }

  let currentUsageId = null;
  let currentFilamentId = null;

  // Handle modal show event - populate with usage details
  deleteModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget; // Button that triggered the modal
    
    // Extract data from button attributes
    currentUsageId = button.getAttribute("data-usage-id");
    currentFilamentId = button.closest("[data-filament-id]")?.getAttribute("data-filament-id") || 
                        window.location.pathname.split("/")[2]; // Extract from URL if not in DOM
    
    const printName = button.getAttribute("data-print-name");
    const component = button.getAttribute("data-component");
    const weight = button.getAttribute("data-weight");
    const timestamp = button.getAttribute("data-timestamp");
    const isMulticolor = button.getAttribute("data-is-multicolor") === "true";

    // Update modal content
    document.getElementById("modal-timestamp").textContent = timestamp;
    document.getElementById("modal-print-name").textContent = printName;
    document.getElementById("modal-component").textContent = component;
    document.getElementById("modal-weight").textContent = weight;
    
    // Show/hide multicolor warning
    const multicolorWarning = document.getElementById("multicolor-warning");
    const pluralFilaments = document.getElementById("plural-filaments");
    
    if (multicolorWarning && pluralFilaments) {
      if (isMulticolor) {
        multicolorWarning.style.display = "block";
        pluralFilaments.style.display = "inline";
      } else {
        multicolorWarning.style.display = "none";
        pluralFilaments.style.display = "none";
      }
    }
  });

  // Handle delete confirmation
  const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener("click", function () {
      if (!currentUsageId || !currentFilamentId) {
        console.error("Missing usage or filament ID");
        return;
      }

      // Disable button and show loading state
      confirmDeleteBtn.disabled = true;
      confirmDeleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...';

      // Make AJAX request to delete
      fetch(`/filaments/${currentFilamentId}/usage/${currentUsageId}/delete`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        credentials: "same-origin",
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          if (data.success) {
            // Close modal
            const modalInstance = bootstrap.Modal.getInstance(deleteModal);
            modalInstance.hide();

            // Show success message and reload page
            // Reloading ensures all data (totals, progress bars, etc.) is accurate
            window.location.reload();
          } else {
            throw new Error(data.error || "Failed to delete usage");
          }
        })
        .catch((error) => {
          console.error("Error deleting usage:", error);
          alert("Error deleting usage record. Please try again.");
          
          // Re-enable button
          confirmDeleteBtn.disabled = false;
          confirmDeleteBtn.innerHTML = '<i class="bi bi-trash"></i> Delete Usage';
        });
    });
  }

  // Reset button state when modal is hidden
  deleteModal.addEventListener("hidden.bs.modal", function () {
    if (confirmDeleteBtn) {
      confirmDeleteBtn.disabled = false;
      confirmDeleteBtn.innerHTML = '<i class="bi bi-trash"></i> Delete Usage';
    }
  });
}
