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

  // Initialize delete usage modal
  initializeDeleteUsageModal();

  // Initialize duplicate usage handlers
  initializeDuplicateUsageHandlers();
});

// ========================================
// DELETE USAGE FUNCTIONALITY
// ========================================

/**
 * Initialize delete usage modal event handlers
 */
function initializeDeleteUsageModal() {
  const deleteModal = document.getElementById("deleteUsageModal");
  if (!deleteModal) return;

  const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");

  // Store usage data when modal is opened
  let currentUsageId = null;
  let currentFilamentId = null;
  let isMulticolor = false;

  // Handle modal show event - populate modal with usage details
  deleteModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget; // Button that triggered the modal

    // Extract data attributes
    currentUsageId = button.getAttribute("data-usage-id");
    const printName = button.getAttribute("data-print-name");
    const component = button.getAttribute("data-component");
    const weight = button.getAttribute("data-weight");
    const timestamp = button.getAttribute("data-timestamp");
    isMulticolor = button.getAttribute("data-is-multicolor") === "true";

    // Get filament ID from current page URL (assumes URL pattern /filaments/{id}/history)
    const urlParts = window.location.pathname.split("/");
    currentFilamentId = urlParts[2]; // Gets the ID from /filaments/{id}/history

    // Populate modal fields
    document.getElementById("modal-timestamp").textContent = timestamp;
    document.getElementById("modal-print-name").textContent = printName;
    document.getElementById("modal-component").textContent = component;
    document.getElementById("modal-weight").textContent = weight;

    // Show/hide multicolor warning
    const multicolorWarning = document.getElementById("multicolor-warning");
    const pluralFilaments = document.getElementById("plural-filaments");

    if (isMulticolor) {
      multicolorWarning.style.display = "block";
      pluralFilaments.style.display = "inline";
    } else {
      multicolorWarning.style.display = "none";
      pluralFilaments.style.display = "none";
    }
  });

  // Handle confirm delete button click
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener("click", function () {
      if (!currentUsageId || !currentFilamentId) {
        console.error("Missing usage or filament ID");
        return;
      }

      // Disable button and show loading state
      confirmDeleteBtn.disabled = true;
      confirmDeleteBtn.innerHTML =
        '<i class="bi bi-hourglass-split"></i> Deleting...';

      // Send delete request
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

            // Show success message
            const message = data.is_multicolor
              ? `Multicolor print deleted successfully. Weight restored to ${data.filaments_updated ? data.filaments_updated.length : "multiple"} filaments.`
              : `Usage deleted successfully. ${data.weight_restored.toFixed(1)}g restored to filament.`;

            // Create a flash message (you might want to style this better)
            showFlashMessage(message, "success");

            // Reload page after short delay to show updated data
            setTimeout(() => {
              window.location.reload();
            }, 1000);
          } else {
            throw new Error(data.error || "Failed to delete usage");
          }
        })
        .catch((error) => {
          console.error("Error deleting usage:", error);

          // Re-enable button
          confirmDeleteBtn.disabled = false;
          confirmDeleteBtn.innerHTML =
            '<i class="bi bi-trash"></i> Delete Usage';

          // Show error message
          showFlashMessage(`Error: ${error.message}`, "danger");
        });
    });
  }
}

/**
 * Show a flash message at the top of the page
 * @param {string} message - Message text
 * @param {string} category - Bootstrap alert category (success, danger, warning, info)
 */
function showFlashMessage(message, category) {
  // Find or create flash messages container
  let container = document.querySelector(".container.mt-4");
  if (!container) {
    container = document.querySelector(".container");
  }

  const alert = document.createElement("div");
  alert.className = `alert alert-${category} alert-dismissible fade show`;
  alert.role = "alert";
  alert.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;

  // Insert at the top of the container
  container.insertBefore(alert, container.firstChild);

  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    alert.classList.remove("show");
    setTimeout(() => alert.remove(), 150);
  }, 5000);
}

// ========================================
// DUPLICATE USAGE FUNCTIONALITY
// ========================================

/**
 * Handle duplicate usage action
 * @param {number} filamentId - The filament ID
 * @param {number} usageId - The usage/print history ID to duplicate
 * @param {string} printName - The print name (for user feedback)
 * @param {boolean} isMulticolor - Whether this is a multicolor print
 */
function handleDuplicateUsage(filamentId, usageId, printName, isMulticolor) {
  // Send duplicate request
  fetch(`/filaments/${filamentId}/usage/${usageId}/duplicate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    credentials: "same-origin",
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((data) => {
          throw new Error(
            data.error || `HTTP error! status: ${response.status}`,
          );
        });
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        // Show success message
        const message = isMulticolor
          ? `Multicolor print "${printName}" duplicated successfully across ${data.filaments_updated ? data.filaments_updated.length : "multiple"} filaments!`
          : `Print "${printName}" duplicated successfully!`;

        showFlashMessage(message, "success");

        // Reload page after short delay to show the duplicated print
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        throw new Error(data.error || "Failed to duplicate print");
      }
    })
    .catch((error) => {
      console.error("Error duplicating print:", error);
      showFlashMessage(`Error: ${error.message}`, "danger");
    });
}

/**
 * Initialize duplicate usage handlers
 */
function initializeDuplicateUsageHandlers() {
  // Find all duplicate buttons
  const duplicateButtons = document.querySelectorAll(".duplicate-usage");

  duplicateButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();

      // Extract data attributes
      const filamentId = this.getAttribute("data-filament-id");
      const usageId = this.getAttribute("data-usage-id");
      const printName = this.getAttribute("data-print-name");
      const isMulticolor = this.getAttribute("data-is-multicolor") === "true";

      // Confirm action with user
      const confirmMessage = isMulticolor
        ? `Duplicate this multicolor print "${printName}"? This will create a new print across all filaments in the group.`
        : `Duplicate print "${printName}"?`;

      if (confirm(confirmMessage)) {
        handleDuplicateUsage(filamentId, usageId, printName, isMulticolor);
      }
    });
  });
}
