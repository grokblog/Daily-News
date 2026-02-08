/**
 * Main JavaScript
 * Handles theme toggle, sharing, and interactions
 */

// ==================== Theme Management ====================
class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.theme);
        this.setupToggle();
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.theme = theme;
        localStorage.setItem('theme', theme);
    }

    toggle() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }

    setupToggle() {
        const toggleBtn = document.getElementById('themeToggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
        }
    }
}

// ==================== Social Sharing ====================
class SocialShare {
    constructor() {
        this.setupShareButtons();
    }

    setupShareButtons() {
        const shareButtons = document.querySelectorAll('[data-share]');
        shareButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const platform = e.currentTarget.getAttribute('data-share');
                this.share(platform);
            });
        });
    }

    share(platform) {
        const url = encodeURIComponent(window.location.href);
        const title = encodeURIComponent(document.title);
        const text = encodeURIComponent(
            document.querySelector('meta[name="description"]')?.content || ''
        );

        let shareUrl;

        switch (platform) {
            case 'facebook':
                shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
                break;
            case 'twitter':
                shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
                break;
            case 'whatsapp':
                shareUrl = `https://wa.me/?text=${title}%20${url}`;
                break;
            case 'linkedin':
                shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${url}`;
                break;
            case 'telegram':
                shareUrl = `https://t.me/share/url?url=${url}&text=${title}`;
                break;
            default:
                return;
        }

        window.open(shareUrl, '_blank', 'width=600,height=400');
    }
}

// ==================== Mobile Menu ====================
class MobileMenu {
    constructor() {
        this.isOpen = false;
        this.init();
    }

    init() {
        const toggle = document.getElementById('mobileMenuToggle');
        if (toggle) {
            toggle.addEventListener('click', () => this.toggle());
        }
    }

    toggle() {
        this.isOpen = !this.isOpen;
        const menu = document.querySelector('.nav-menu');
        const toggle = document.getElementById('mobileMenuToggle');

        if (this.isOpen) {
            menu.style.display = 'flex';
            menu.style.flexDirection = 'column';
            menu.style.position = 'absolute';
            menu.style.top = 'var(--navbar-height)';
            menu.style.left = '0';
            menu.style.right = '0';
            menu.style.background = 'var(--color-bg)';
            menu.style.padding = 'var(--spacing-xl)';
            menu.style.boxShadow = 'var(--shadow-lg)';
            toggle.classList.add('active');
        } else {
            menu.style.display = '';
            menu.style.flexDirection = '';
            menu.style.position = '';
            menu.style.top = '';
            menu.style.left = '';
            menu.style.right = '';
            menu.style.background = '';
            menu.style.padding = '';
            menu.style.boxShadow = '';
            toggle.classList.remove('active');
        }
    }
}

// ==================== Reading Progress ====================
class ReadingProgress {
    constructor() {
        this.createProgressBar();
        this.setupScroll();
    }

    createProgressBar() {
        const bar = document.createElement('div');
        bar.id = 'reading-progress';
        bar.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 3px;
            background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
            z-index: 9999;
            transition: width 0.1s ease;
        `;
        document.body.appendChild(bar);
        this.bar = bar;
    }

    setupScroll() {
        window.addEventListener('scroll', () => {
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            const scrollPercent = (scrollTop / (documentHeight - windowHeight)) * 100;
            this.bar.style.width = `${Math.min(scrollPercent, 100)}%`;
        });
    }
}

// ==================== Lazy Loading Images ====================
class LazyLoader {
    constructor() {
        this.setupObserver();
    }

    setupObserver() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src || img.src;
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[loading="lazy"]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }
}

// ==================== Smooth Scroll ====================
class SmoothScroll {
    constructor() {
        this.setupLinks();
    }

    setupLinks() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
}

// ==================== Copy Link ====================
class CopyLink {
    constructor() {
        this.setupCopyButtons();
    }

    setupCopyButtons() {
        document.querySelectorAll('[data-copy-link]').forEach(btn => {
            btn.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(window.location.href);
                    this.showToast('Link copied to clipboard!');
                } catch (err) {
                    console.error('Failed to copy:', err);
                }
            });
        });
    }

    showToast(message) {
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--color-success);
            color: white;
            padding: var(--spacing-md) var(--spacing-lg);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// ==================== Table of Contents ====================
class TableOfContents {
    constructor() {
        this.generateTOC();
    }

    generateTOC() {
        const content = document.querySelector('.article-content');
        if (!content) return;

        const headings = content.querySelectorAll('h2, h3');
        if (headings.length < 3) return; // Only show TOC if there are 3+ headings

        const toc = document.createElement('div');
        toc.className = 'table-of-contents';
        toc.innerHTML = '<h4>Table of Contents</h4><ul></ul>';

        const list = toc.querySelector('ul');

        headings.forEach((heading, index) => {
            // Add ID to heading if it doesn't have one
            if (!heading.id) {
                heading.id = `heading-${index}`;
            }

            const li = document.createElement('li');
            li.className = heading.tagName.toLowerCase();

            const a = document.createElement('a');
            a.href = `#${heading.id}`;
            a.textContent = heading.textContent;

            li.appendChild(a);
            list.appendChild(li);
        });

        // Insert TOC after first paragraph
        const firstPara = content.querySelector('p');
        if (firstPara) {
            firstPara.after(toc);
        }
    }
}

// ==================== Analytics ====================
class Analytics {
    constructor() {
        this.trackPageView();
        this.trackEngagement();
    }

    trackPageView() {
        // Placeholder for analytics tracking
        console.log('Page view tracked:', window.location.pathname);
    }

    trackEngagement() {
        // Track time on page
        const startTime = Date.now();

        window.addEventListener('beforeunload', () => {
            const timeSpent = Math.round((Date.now() - startTime) / 1000);
            console.log('Time spent on page:', timeSpent, 'seconds');
        });

        // Track scroll depth
        let maxScroll = 0;
        window.addEventListener('scroll', () => {
            const scrollPercent = Math.round(
                (window.pageYOffset / (document.documentElement.scrollHeight - window.innerHeight)) * 100
            );
            maxScroll = Math.max(maxScroll, scrollPercent);
        });

        window.addEventListener('beforeunload', () => {
            console.log('Max scroll depth:', maxScroll, '%');
        });
    }
}

// ==================== Initialize Everything ====================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all modules
    new ThemeManager();
    new SocialShare();
    new MobileMenu();
    new ReadingProgress();
    new LazyLoader();
    new SmoothScroll();
    new CopyLink();
    new TableOfContents();
    new Analytics();

    // Add loaded class to body
    document.body.classList.add('loaded');

    console.log('✨ Blog initialized successfully');
});

// ==================== Service Worker Registration ====================
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered:', registration);
            })
            .catch(error => {
                console.log('SW registration failed:', error);
            });
    });
}
