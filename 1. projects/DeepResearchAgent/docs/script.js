// AgentOrchestra Website JavaScript

// 页面加载动画处理 - 添加在文件开头
window.addEventListener('load', function() {
    setTimeout(() => {
        const loader = document.getElementById('pageLoader');
        if (loader) {
            loader.style.opacity = '0';
            loader.style.visibility = 'hidden';
            document.body.classList.add('loaded');
        }
    }, 1500);
});

// 如果页面已经加载完成，立即隐藏加载器
if (document.readyState === 'complete') {
    const loader = document.getElementById('pageLoader');
    if (loader) {
        loader.style.opacity = '0';
        loader.style.visibility = 'hidden';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // 鼠标跟随效果
    function createMouseFollower() {
        const follower = document.getElementById('mouseFollower');
        if (!follower) return;
        
        document.addEventListener('mousemove', (e) => {
            follower.style.transform = `translate(${e.clientX - 10}px, ${e.clientY - 10}px)`;
        });

        // 悬停效果
        const hoverElements = document.querySelectorAll('a, button, .card-3d');
        hoverElements.forEach(element => {
            element.addEventListener('mouseenter', () => {
                follower.classList.add('hover');
            });
            element.addEventListener('mouseleave', () => {
                follower.classList.remove('hover');
            });
        });
    }

    // 粒子背景效果
    function createParticles() {
        const container = document.getElementById('particlesBg');
        if (!container) return;
        
        const particleCount = 50;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            // 随机大小和位置
            const size = Math.random() * 4 + 2;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;
            particle.style.animationDelay = `${Math.random() * 6}s`;
            particle.style.animationDuration = `${Math.random() * 3 + 3}s`;
            
            container.appendChild(particle);
        }
    }

    // 滚动动画观察器
    function initScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate');
                }
            });
        }, observerOptions);

        // 观察所有需要动画的元素
        const animatedElements = document.querySelectorAll('.scroll-animate, .scroll-animate-left, .scroll-animate-right');
        animatedElements.forEach(el => observer.observe(el));
    }

    // 初始化动态效果
    createMouseFollower();
    createParticles();
    initScrollAnimations();

    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);

    // Observe all sections for fade-in animation
    const sections = document.querySelectorAll('section');
    sections.forEach(section => {
        section.classList.add('section-fade');
        observer.observe(section);
    });

    // Navigation active state
    const navItems = document.querySelectorAll('nav a[href^="#"]');
    const sectionsForNav = document.querySelectorAll('section[id]');

    function updateActiveNav() {
        let current = '';
        sectionsForNav.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (window.pageYOffset >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });

        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href') === `#${current}`) {
                item.classList.add('active');
            }
        });
    }

    window.addEventListener('scroll', updateActiveNav);
    updateActiveNav();

    // Parallax effect for hero section
    const heroSection = document.querySelector('.bg-gradient-to-br');
    if (heroSection) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            heroSection.style.transform = `translateY(${rate}px)`;
        });
    }

    // Typing animation for hero title
    const heroTitle = document.getElementById('heroTitle');
    if (heroTitle) {
        const text = heroTitle.textContent;
        heroTitle.textContent = '';
        heroTitle.classList.add('typewriter-cursor');
        
        let i = 0;
        function typeWriter() {
            if (i < text.length) {
                heroTitle.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            } else {
                setTimeout(() => {
                    heroTitle.classList.remove('typewriter-cursor');
                }, 1000);
            }
        }
        
        // 延迟开始打字效果
        setTimeout(typeWriter, 2000);
    }

    // Counter animation for statistics
    const counters = document.querySelectorAll('.text-2xl.font-bold');
    const counterObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseFloat(counter.textContent.replace(/[^\d.]/g, ''));
                const duration = 2000;
                const step = target / (duration / 16);
                let current = 0;
                
                const timer = setInterval(() => {
                    current += step;
                    if (current >= target) {
                        current = target;
                        clearInterval(timer);
                    }
                    counter.textContent = current.toFixed(2);
                }, 16);
                
                counterObserver.unobserve(counter);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => {
        counterObserver.observe(counter);
    });

    // Hover effects for cards
    const cards = document.querySelectorAll('.bg-white.p-6.rounded-xl');
    cards.forEach(card => {
        card.classList.add('card-hover');
    });

    // Image hover effects
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.classList.add('img-hover');
    });

    // Mobile menu toggle (if needed)
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Back to top button
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = `
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path>
        </svg>
    `;
    backToTopButton.className = 'fixed bottom-8 right-8 bg-primary-600 text-white p-3 rounded-full shadow-lg hover:bg-primary-700 transition-all duration-300 opacity-0 pointer-events-none z-50';
    backToTopButton.id = 'back-to-top';
    document.body.appendChild(backToTopButton);

    // Show/hide back to top button
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.classList.remove('opacity-0', 'pointer-events-none');
            backToTopButton.classList.add('opacity-100');
        } else {
            backToTopButton.classList.add('opacity-0', 'pointer-events-none');
            backToTopButton.classList.remove('opacity-100');
        }
    });

    // Back to top functionality
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Loading animation
    const loadingElements = document.querySelectorAll('.loading-dots');
    loadingElements.forEach(element => {
        element.style.display = 'inline-block';
    });

    // Copy to clipboard functionality for code blocks
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        const copyButton = document.createElement('button');
        copyButton.textContent = 'Copy';
        copyButton.className = 'absolute top-2 right-2 bg-gray-800 text-white px-2 py-1 rounded text-sm hover:bg-gray-700 transition-colors';
        
        const pre = block.parentElement;
        pre.style.position = 'relative';
        pre.appendChild(copyButton);
        
        copyButton.addEventListener('click', function() {
            navigator.clipboard.writeText(block.textContent).then(() => {
                copyButton.textContent = 'Copied!';
                setTimeout(() => {
                    copyButton.textContent = 'Copy';
                }, 2000);
            });
        });
    });

    // Lazy loading for images
    const lazyImages = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    lazyImages.forEach(img => {
        imageObserver.observe(img);
    });

    // Performance optimization: Debounce scroll events
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Apply debouncing to scroll events
    const debouncedUpdateActiveNav = debounce(updateActiveNav, 10);
    window.addEventListener('scroll', debouncedUpdateActiveNav);

    // Console welcome message
    console.log(`
    🎼 Welcome to AgentOrchestra! 🎼
    
    A Hierarchical Multi-Agent Framework for General-Purpose Task Solving
    
    📄 Paper: https://arxiv.org/abs/2506.12508
    💻 Code: https://github.com/SkyworkAI/DeepResearchAgent
    
    Happy exploring! 🚀
    `);

    // 柱状图动画函数
    function animateCharts() {
      const chartRows = document.querySelectorAll('.chart-row');
      
      // 创建观察器来触发动画
      const chartObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
          if (entry.isIntersecting) {
            const row = entry.target;
            const bar = row.querySelector('.chart-bar');
            const value = row.querySelector('.chart-value');
            const targetWidth = bar.getAttribute('data-width');
            const score = row.getAttribute('data-score');
            
            // 延迟动画，让每行依次出现
            setTimeout(() => {
              // 显示行
              row.classList.add('animate');
              
              // 延迟后开始填充柱状图
              setTimeout(() => {
                // 设置目标宽度
                bar.style.setProperty('--target-width', targetWidth + '%');
                bar.classList.add('animate');
                
                // 数字计数动画
                animateCounter(value, score);
                
              }, 300);
            }, index * 200);
            
            chartObserver.unobserve(row);
          }
        });
      }, {
        threshold: 0.3,
        rootMargin: '0px 0px -50px 0px'
      });
      
      // 观察所有图表行
      chartRows.forEach(row => {
        chartObserver.observe(row);
      });
    }

    // 数字计数动画函数
    function animateCounter(element, targetValue) {
      const target = parseFloat(targetValue);
      const duration = 1500;
      const step = target / (duration / 16);
      let current = 0;
      
      const timer = setInterval(() => {
        current += step;
        if (current >= target) {
          current = target;
          clearInterval(timer);
          element.classList.add('show');
        }
        element.textContent = current.toFixed(2);
      }, 16);
    }

    // 在 DOMContentLoaded 事件中调用动画函数
    animateCharts();

    // 添加重新播放动画的功能
    function replayChartAnimation() {
      const chartRows = document.querySelectorAll('.chart-row');
      const chartBars = document.querySelectorAll('.chart-bar');
      const chartValues = document.querySelectorAll('.chart-value');
      
      // 重置所有元素
      chartRows.forEach(row => {
        row.classList.remove('animate');
      });
      
      chartBars.forEach(bar => {
        bar.classList.remove('animate');
        bar.style.width = '0%';
      });
      
      chartValues.forEach(value => {
        value.classList.remove('show');
        value.style.opacity = '0';
      });
      
      // 重新开始动画
      setTimeout(() => {
        animateCharts();
      }, 500);
    }

    // 添加点击重新播放功能（可选）
    document.addEventListener('DOMContentLoaded', function() {
      const chartContainer = document.querySelector('.bg-white.p-8.rounded-xl.shadow-sm');
      if (chartContainer) {
        chartContainer.addEventListener('click', function(e) {
          // 如果点击的是图表区域但不是具体的柱状图，则重新播放动画
          if (e.target === this || e.target.classList.contains('space-y-4')) {
            replayChartAnimation();
          }
        });
        
        // 添加提示
        chartContainer.style.cursor = 'pointer';
        chartContainer.title = '点击重新播放动画';
      }
    });
});
