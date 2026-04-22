/**
 * ============================================================
 * HUSTLE & CRACK — Global JavaScript Module
 * Security Layer · UI Animations · Form Helpers · Navigation
 * Designed by Rishikesh Kumar Bharti
 * ============================================================
 */

(function() {
    'use strict';

    // ======================= SECURITY LAYER =======================
    
    // 1. Disable right-click context menu globally
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        return false;
    });

    // 2. Disable dangerous keyboard shortcuts (F12, Ctrl+Shift+I, Ctrl+U, Ctrl+S, etc.)
    document.addEventListener('keydown', function(e) {
        // Block F12
        if (e.key === 'F12') {
            e.preventDefault();
            return false;
        }
        // Block Ctrl+Shift+I (Inspect), Ctrl+Shift+J (Console), Ctrl+Shift+C (Element picker)
        if (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) {
            e.preventDefault();
            return false;
        }
        // Block Ctrl+U (View Source)
        if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            return false;
        }
        // Block Ctrl+S (Save page)
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            return false;
        }
        // Block Ctrl+P (Print) optional – to protect PDF generation? Not necessary but can be added
        // if (e.ctrlKey && e.key === 'p') {
        //     e.preventDefault();
        //     return false;
        // }
        // Block Ctrl+C (Copy) – many sites do this, but may break UX; we'll allow copy but restrict via CSS? 
        // Usually we allow copy for text but disable right-click. We'll leave Ctrl+C enabled for better UX.
        // However, if you want to block copying entirely, uncomment the next lines:
        // if (e.ctrlKey && e.key === 'c') {
        //     e.preventDefault();
        //     return false;
        // }
    });

    // 3. Disable image dragging globally (protects branding & photos)
    const allImages = document.querySelectorAll('img');
    allImages.forEach(img => {
        img.setAttribute('draggable', 'false');
        img.addEventListener('dragstart', function(e) {
            e.preventDefault();
            return false;
        });
        // Also disable right-click on images individually (redundant but safe)
        img.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            return false;
        });
    });
    // For dynamically added images, use MutationObserver
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeName === 'IMG') {
                    node.setAttribute('draggable', 'false');
                    node.addEventListener('dragstart', function(e) { e.preventDefault(); });
                    node.addEventListener('contextmenu', function(e) { e.preventDefault(); });
                } else if (node.querySelectorAll) {
                    node.querySelectorAll('img').forEach(img => {
                        img.setAttribute('draggable', 'false');
                        img.addEventListener('dragstart', function(e) { e.preventDefault(); });
                        img.addEventListener('contextmenu', function(e) { e.preventDefault(); });
                    });
                }
            });
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // ======================= GLOBAL UI ANIMATIONS =======================
    
    // 4. Smooth Page Transition (fade effect when clicking internal links)
    //    This function adds a fade-out/in effect during navigation.
    //    It intercepts clicks on anchor tags that point to internal pages (same origin).
    function initSmoothTransitions() {
        const links = document.querySelectorAll('a[href]');
        links.forEach(link => {
            // Only process internal links (same origin, not external, not hash links, not javascript:)
            const href = link.getAttribute('href');
            if (href && href.startsWith('/') && !href.startsWith('//') && !href.startsWith('javascript:')) {
                link.addEventListener('click', function(e) {
                    // Allow Ctrl/Cmd+Click to open in new tab without transition
                    if (e.ctrlKey || e.metaKey) return;
                    e.preventDefault();
                    const targetUrl = href;
                    // Fade out body content
                    document.body.style.transition = 'opacity 0.3s ease';
                    document.body.style.opacity = '0';
                    setTimeout(() => {
                        window.location.href = targetUrl;
                    }, 300);
                });
            }
        });
    }
    // Run after DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSmoothTransitions);
    } else {
        initSmoothTransitions();
    }
    // Restore opacity when page loads (in case of direct navigation)
    window.addEventListener('pageshow', function() {
        document.body.style.transition = '';
        document.body.style.opacity = '1';
    });

    // 5. Greeting System (Toast notification with time-based greeting)
    function showGreetingToast() {
        const now = new Date();
        const hour = now.getHours();
        let greeting = '';
        if (hour >= 5 && hour < 12) greeting = 'Good Morning';
        else if (hour >= 12 && hour < 17) greeting = 'Good Afternoon';
        else if (hour >= 17 && hour < 21) greeting = 'Good Evening';
        else greeting = 'Good Night';
        
        const message = `${greeting}, Rishikesh! Welcome back to Hustle & Crack.`;
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'global-toast';
        toast.innerHTML = `<i class="fas fa-crown" style="margin-right:8px;"></i> ${message}`;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(10, 10, 12, 0.95);
            backdrop-filter: blur(10px);
            border-left: 4px solid #C9A84C;
            color: #F0EDE6;
            padding: 12px 20px;
            border-radius: 12px;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.85rem;
            z-index: 9999;
            box-shadow: 0 5px 20px rgba(0,0,0,0.5);
            transition: transform 0.3s ease, opacity 0.3s ease;
            transform: translateX(120%);
            opacity: 0;
        `;
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        }, 100);
        
        // Auto remove after 4 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(120%)';
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 400);
        }, 4000);
    }
    // Show greeting only once per session (optional: check sessionStorage)
    if (!sessionStorage.getItem('greetingShown')) {
        sessionStorage.setItem('greetingShown', 'true');
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', showGreetingToast);
        } else {
            showGreetingToast();
        }
    }

    // ======================= FORM VALIDATIONS (Global Helper) =======================
    
    // 6. Validate phone number (exactly 10 digits)
    window.validatePhoneNumber = function(phoneValue) {
        const phoneRegex = /^\d{10}$/;
        return phoneRegex.test(phoneValue);
    };
    
    // Optional: Auto-attach phone validation to any input with class 'phone-input' or data-validate="phone"
    function autoBindPhoneValidation() {
        const phoneInputs = document.querySelectorAll('input[type="tel"], input.phone-input, input[data-validate="phone"]');
        phoneInputs.forEach(input => {
            // Remove existing listener to avoid duplicates
            input.removeEventListener('blur', phoneValidationHandler);
            input.addEventListener('blur', phoneValidationHandler);
        });
    }
    function phoneValidationHandler(e) {
        const input = e.target;
        const value = input.value.trim();
        if (value && !window.validatePhoneNumber(value)) {
            // Show error message if not already showing
            let errorSpan = input.parentNode.querySelector('.phone-error');
            if (!errorSpan) {
                errorSpan = document.createElement('span');
                errorSpan.className = 'phone-error';
                errorSpan.style.cssText = 'color:#FF7B7B; font-size:0.7rem; margin-top:4px; display:block;';
                input.parentNode.appendChild(errorSpan);
            }
            errorSpan.innerText = '❌ Phone number must be exactly 10 digits.';
            input.classList.add('error');
        } else {
            const errorSpan = input.parentNode.querySelector('.phone-error');
            if (errorSpan) errorSpan.remove();
            input.classList.remove('error');
        }
    }
    // Run on DOM ready and also observe dynamically added forms
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoBindPhoneValidation);
    } else {
        autoBindPhoneValidation();
    }
    // Re-run when new forms are added via AJAX (MutationObserver)
    const formObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                autoBindPhoneValidation();
            }
        });
    });
    formObserver.observe(document.body, { childList: true, subtree: true });

    // ======================= ACTIVE LINK HIGHLIGHTING =======================
    
    // 7. Automatically add 'active' class to current page navigation link
    function highlightActiveLink() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.main-nav a, nav a, .nav-link');
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && href !== '#' && href !== '') {
                // Normalize paths: remove leading/trailing slashes for comparison
                let linkPath = href.split('?')[0]; // remove query params
                if (linkPath.startsWith('/')) linkPath = linkPath.substring(1);
                let currPath = currentPath;
                if (currPath.startsWith('/')) currPath = currPath.substring(1);
                if (currPath === linkPath) {
                    link.classList.add('active');
                } else if (linkPath !== '' && currPath.includes(linkPath) && linkPath !== '/') {
                    // Optional: partial match for deeper nesting
                    // but we'll keep exact match for clarity
                }
            }
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', highlightActiveLink);
    } else {
        highlightActiveLink();
    }

    // Optional: Re-run when using pushState (for SPAs) – but not needed for standard Flask
    window.addEventListener('popstate', function() {
        highlightActiveLink();
    });

    // ======================= ADDITIONAL UTILITIES =======================
    
    // Expose a global API for other scripts
    window.HustleCrack = {
        // Security methods
        protectImages: () => {
            // re-run protection for dynamically added images
            document.querySelectorAll('img').forEach(img => {
                img.setAttribute('draggable', 'false');
                img.addEventListener('dragstart', (e) => e.preventDefault());
                img.addEventListener('contextmenu', (e) => e.preventDefault());
            });
        },
        // Show custom toast message (reusable)
        showToast: (message, type = 'info') => {
            const toast = document.createElement('div');
            toast.className = 'global-toast';
            let icon = 'fas fa-info-circle';
            if (type === 'success') icon = 'fas fa-check-circle';
            if (type === 'error') icon = 'fas fa-exclamation-triangle';
            toast.innerHTML = `<i class="${icon}" style="margin-right:8px; color:#C9A84C;"></i> ${message}`;
            toast.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(10, 10, 12, 0.95);
                backdrop-filter: blur(10px);
                border-left: 4px solid #C9A84C;
                color: #F0EDE6;
                padding: 12px 20px;
                border-radius: 12px;
                font-family: 'DM Sans', sans-serif;
                font-size: 0.85rem;
                z-index: 9999;
                box-shadow: 0 5px 20px rgba(0,0,0,0.5);
                transition: transform 0.3s ease, opacity 0.3s ease;
                transform: translateX(120%);
                opacity: 0;
            `;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.transform = 'translateX(0)';
                toast.style.opacity = '1';
            }, 100);
            setTimeout(() => {
                toast.style.transform = 'translateX(120%)';
                toast.style.opacity = '0';
                setTimeout(() => {
                    if (toast.parentNode) toast.parentNode.removeChild(toast);
                }, 400);
            }, 4000);
        }
    };
    
    // Console log to confirm script loaded (optional, remove in production)
    console.log('✅ Hustle & Crack Global JS loaded — Security & UI enhancements active.');
})();