function PhEnhancer() {
    // // To avoid showing the footer with broken styles
    // var footerElem = document.querySelector('.ph-footer');
    //     footerElem && (footerElem.style.visibility = 'hidden');
    var splElements = ['ph-search-results-v1', 'ph-search-results-v2', 'ph-facets-v1'];
    var recomWidget = ['ph-profile-recommendations-v2', 'ph-profile-recommendations-v1'];
    var templatingEngine, phVdom, actionAfterLoad;
    var parentWidgetMap = {};
    var userAgent = navigator.userAgent;
    var isIe = userAgent && (userAgent.indexOf('Trident') != -1 || userAgent.indexOf('MSIE') != -1);
    var isInterSectionSupports = !isIe;
    var widgetsIgnoreList = [
        'ph-near-By-jobs-v2',
        'ph-recom-jobs-browsing-history-v3',
        'ph-people-also-viewed-v2',
        'ph-job-cart-v3',
        'ph-targeted-jobs-v2',
        'ph-similar-jobs-v2',
        'ph-recently-viewed-jobs-v3',
        'ph-profile-recommendations-v2'
    ];

    var isEnhancedAllWidgets = false;
    const AURELIA_WIDGET_SELECTOR = '[as-element]:not([type="static"])';
    const NON_DSD_GLOBAL_VIEWS_DDO_KEY = 'getWidgetMetaData';

    const UN_ENHANCED_AURELIA_WIDGET_SELECTOR =
        '.ph-widget[aurelia-global-widget] [as-element]:not([as-element="null"]):not([type="static"]):not([au-target-id])';

    const isDdoEagerLoaded = {};
    const configuredMakeEagerLoadDdos = [];

    const CSRF_TOKEN = 'csrfToken';

    const DDO_KEY_GET_WIDGET_VERSIONS = 'getWidgetVersions';
    const AURELIA_DYNAMIC_WIDGET_SELECTOR = '[as-element]:not([type="static"])';
    const NON_DS_CONTENT_FETCH_DDO_KEY = 'canvasGetWidgetContent';
    const WIDGET_VERSIONS_STORAGE_KEY = 'ph_au_widget_versions';
    const CONTENT_STORAGE_KEY_PREFIX = 'ph_au_content_';
    const TRANSLATIONS_STORAGE_KEY_PREFIX = 'ph_au_translations_';

    const DS_NON_DS_VS_PAGE_STATE_MAP = {
        'results': 'exists',
        'no-results': 'expired',
    }


    function fetchDOM() {
        var bodyElem = document.querySelector('body');
        phVdom = bodyElem.cloneNode(true);
    }

    function queryWidgetElem(selector) {
        if (selector) {
            var widgetElem;
            var sel = '[instance-id="' + selector + '"]';
            widgetElem = document.querySelector(sel);
            if (!widgetElem) {
                sel = '[as-element="' + selector + '"]';
                widgetElem = document.querySelector(sel);
            }
            return widgetElem;
        }
    }
    function swapAsElement(key, widgetElem) { }

    function attachEventListeners() {
        var actionableElems = document.querySelectorAll('[phae]');
        if (actionableElems) {
            var actionableElemsLen = actionableElems.length;
            for (var j = 0; j < actionableElemsLen; j++) {
                var actionableElem = actionableElems[j];
                var actionRef = actionableElem.getAttribute('phae');
                var actionType = actionableElem.getAttribute('phae-type');
                var widgetElem = queryWidgetElem(actionRef, actionableElem);

                if (widgetElem) {
                    swapAsElement('as-element', widgetElem);
                }
                actionType = actionType || 'focus';
                actionableElem.addEventListener(actionType, handleLoadWidget);
            }
        }

        document.addEventListener('keyup', renderAllWidgets);
        document.addEventListener('getUserProfileData', loadRecomWidget);
    }

    function getSections(root, elems) {
        //console.time('toplevel-queryselect>getSections')
        if (root) {
            var children = root.children;
            var childElemCount = root.childElementCount;
            for (var i = 0; i < childElemCount; i++) {
                var childElem = children[i];
                if (childElem && childElem.classList.contains('ph-widget')) {
                    elems.push(childElem);
                } else {
                    if (childElem.childElementCount) {
                        getSections(childElem, elems);
                    }
                }
            }
        }
        //console.timeEnd('toplevel-queryselect>getSections')
    }

    function renderAllWidgets(ev) {
        if (isEnhancedAllWidgets) {
            return;
        }
        var keys = [37, 38, 39, 40, 9, 13];
        var keyNameList = ['ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter'];

        var keyCode = ev.keyCode || ev.which || '';
        var keyName = ev.code || ev.key;

        if (keys.indexOf(keyCode) !== -1 || keyNameList.indexOf(keyName) !== -1) {
            enhanceAllWidgets();
            isEnhancedAllWidgets = true;
            document.removeEventListener('keyup', renderAllWidgets);
        }
    }

    function enhanceAllWidgets() {
        if (isEnhancedAllWidgets) {
            return;
        }
        isEnhancedAllWidgets = true;
        var widgetsList = [];
        getSections(document, widgetsList);

        for (var ju = 0; ju < widgetsList.length; ju++) {
            var widgetEnhanced = widgetsList[ju].querySelector('.au-target');
            if (!widgetEnhanced) {
                timerFn(ju, widgetsList[ju]);
            }
        }

        var asLitElems = document.querySelectorAll('[as-lit-tmpl]');
        for (var k = 0; k < asLitElems.length; k++) {
            var widgetEnhanced = widgetsList[k].querySelector('.au-target');
            if (!widgetEnhanced && widgetsList[k].parentElement) {
                timerFn(k, widgetsList[k].parentElement);
            }
        }
    }

    function timerFn(i, wgt) {
        setTimeout(function () {
            var fElem = wgt.firstElementChild && wgt.firstElementChild.getAttribute('data-widget');
            if (fElem && wgt.firstElementChild.nodeName == 'DIV') {
                wgt = wgt.firstElementChild;
            }
            enhanceElem(wgt);
        }, i * 100);
    }

    function loadFramework(lazyLoad = false) {
        var au = lazyLoad ? window.lazyAurelia : window.localAurelia;
        if (!au) {
            require([
                'aurelia-framework',
                'aurelia-loader-default',
                'aurelia-pal-browser',
                lazyLoad ? 'lazy-components' : 'components',
                'aurelia-templating',
                'aurelia-task-queue',
                'aurelia-logging',
                'aurelia-templating-binding',
                'aurelia-polyfills'
            ], function (AF, ALD, PAL, e, AT, ATQ) {
                require(['ph-common'], function (PHC) {
                    //e.default.push('aurelia-templating-resources')
                    require(e.default, function (WM) {
                        PAL.initialize();
                        taskQueue = new ATQ.TaskQueue();
                        var loader = new ALD.DefaultLoader();
                        var aurelia = new AF.Aurelia(loader);
                        aurelia.loader.loadModule('aurelia-framework');
                        if (lazyLoad) {
                            window.lazyAurelia = aurelia;
                        } else {
                            window.localAurelia = aurelia;
                        }
                        aurelia.use
                            .defaultBindingLanguage()
                            .defaultResources()
                            .plugin('ph-common')
                            .globalResources(e.default);
                        var aStart = aurelia.start();
                        aStart.then(function () {
                            handlePostFrameWorkInitiation(lazyLoad);
                        });
                    });
                });
            });
        }
    }
    function getDynamicWidgetData() {
        try {
            const dynamicWidgetData = [];

            const dynamicWidgets = document.querySelectorAll(AURELIA_DYNAMIC_WIDGET_SELECTOR);

            for (let i = 0; i < dynamicWidgets.length; ++i) {
                const dynamicWidget = dynamicWidgets[i];

                const originalView = dynamicWidget.getAttribute('original-view');
                // const theme = dynamicWidget.getAttribute('theme') || 'default'
                const tagName = dynamicWidget.getAttribute('as-element');

                const widgetId = [tagName, originalView].join('-');

                const instanceId = dynamicWidget.getAttribute('instance-id');

                if (instanceId && widgetId) {
                    dynamicWidgetData.push({
                        widgetId,
                        instanceId
                    });
                }
            }

            return dynamicWidgetData;
        } catch (e) {
            console.error(`Error occured while fetching dynamic widget data: ${e}`);
        }
    }

    function prepareFetchContentRequest(dynamicWidgetData) {
        const fetchContentReq = {
            data: {},
            pageId: phApp.pageId,
        };
        for (let i = 0; i < dynamicWidgetData.length; ++i) {
            const { widgetId, instanceId } = dynamicWidgetData[i];
            fetchContentReq.data[instanceId] = widgetId;
        }

        return fetchContentReq;
    }
    function moveWidgetContentToRoot(content) {
        const widgetContent = {};

        function identifyWidgteContentMap(content) {
            try {
                Object.keys(content).forEach((key) => {
                    const value = content[key];
                    if (typeof value === 'object') {
                        const val = identifyWidgteContentMap(value);
                        if (value.type === 'widget') {
                            widgetContent[key] = { contentMap: val };
                            delete content[key];
                        }
                    }
                });

                return content;
            } catch (error) {
                console.error('Error occured while identifying widget content map: ', error);
            }
        }

        content = identifyWidgteContentMap(content);

        return Object.assign(content, widgetContent);
    }

    function splitContentAndBindables(obj) {
        const content = {};
        const bindables = {};

        for (let key in obj) {
            if (typeof obj[key] === 'object' && obj[key] !== null) {
                // Separate `content` and `bindables` into their respective objects
                if (obj[key].hasOwnProperty('contentMap')) {
                    content[key] = { contentMap: obj[key].contentMap };
                }
                if (obj[key].hasOwnProperty('bindables')) {
                    bindables[key] = { bindables: obj[key].bindables };
                }
            }
        }

        return { content, bindables };
    }

    function camelCaseToKebabCase(str) {
        return str.replace(/([a-z0-9]|(?=[A-Z]))([A-Z])/g, '$1-$2').toLowerCase();
    }

    function setBindables(widgetElement, bindableMap) {
        try {
            Object.keys(bindableMap).forEach(function (key) {
                const value = bindableMap[key];
                key = camelCaseToKebabCase(key);
                if (!widgetElement.hasAttribute(key) || (key === 'rk' && widgetElement.getAttribute(key) !== value)) {
                    if (typeof value === 'string') {
                        widgetElement.setAttribute(key, value);
                    } else if (typeof value === 'boolean' || typeof value === 'number') {
                        widgetElement.setAttribute(`${key}.bind`, value.toString());
                    }
                }
            });
        } catch (error) {
            console.error('Error in setBindables', error);
        }

    }

    function setWidgetBindables() {
        const bindables = window.phBindablesStore;
        const widgets = document.querySelectorAll(AURELIA_DYNAMIC_WIDGET_SELECTOR);
        for (let i = 0; i < widgets.length; ++i) {
            const widget = widgets[i];
            const instanceId = widget.getAttribute('instance-id');
            const bindableMap = bindables[instanceId];
            if (bindableMap) {
                setBindables(widget, bindableMap.bindables);
            }
        }
    }


    async function fetchContent() {
        try {
            // First, try to get from localStorage
            const cachedContent = getContentFromStorage();
            if (cachedContent) {
                // Apply cached content immediately
                window.phBindablesStore = cachedContent.bindables;
                window.phContentStore = cachedContent.content;
                phApp.settings = phApp.settings || {};
                phApp.settings = { ...phApp.settings, ...cachedContent.designData };

                // Update localStorage asynchronously in background
                fetchContentFromAPI(true).then((freshContent) => {
                    if (freshContent) {
                        saveContentToStorage(freshContent);
                        // Also update the current stores with fresh data
                        window.phBindablesStore = freshContent.bindables;
                        window.phContentStore = freshContent.content;
                        phApp.settings = { ...phApp.settings, ...freshContent.designData };
                    }
                }).catch((err) => {
                    console.error('Background content update failed:', err);
                });
                return;
            }

            // If not in localStorage, fetch from API and cache
            const contentData = await fetchContentFromAPI();
            if (contentData) {
                // Apply content to global stores
                window.phBindablesStore = contentData.bindables;
                window.phContentStore = contentData.content;
                phApp.settings = phApp.settings || {};
                phApp.settings = { ...phApp.settings, ...contentData.designData };

                // Save to localStorage for next time
                saveContentToStorage(contentData);
            } else {
                console.error('Error occurred while fetching content for dynamic widgets');
            }
        } catch (error) {
            console.error('Error occurred while fetching content for dynamic widgets: ', error);
        }
    }

    async function handlePostFrameWorkInitiation(lazyLoad = false) {
        await fetchContent();
        setWidgetBindables();
        var au = lazyLoad ? window.lazyAurelia : window.localAurelia;
        var q = au.loader.moduleRegistry['aurelia-framework'];
        templatingEngine = au.container.get(q.TemplatingEngine);
        if (phApp && phApp.siteType && phApp.siteType === 'internal') {
            var bodyElem = document.querySelector('body');
            loadLazyImages();
            enhanceElem(bodyElem);
            revertFooterVisibility();
            return;
        }
        loadSpecialElements(null, lazyLoad);
        setResetHeaderWidgets();
        loadHeaderWidgets(lazyLoad);
        setTimeout(function () {
            attachAudienceEventMetaData();
            if (lazyLoad) {
                // TODO: need to handle phw-sticky-top-all can contain au widgets
                loadWidgets('body > section, .ph-page [as-element], .ph-page-deleted [as-element], .ph-footer, .phw-sticky-top-all [as-element]', lazyLoad);
            } else {
                loadWidgets('body > section, .ph-page :not([aurelia-global-widget])>[as-element], .ph-page-deleted :not([aurelia-global-widget])>[as-element], .ph-footer, .phw-sticky-top-all :not([aurelia-global-widget])>[as-element]', lazyLoad);
            }
            initiatePageState();
            loadLazyImages();
            handleSliders();
            handleStickyElem();
        }, 50);
    }

    function attachAudienceEventMetaData() {
        var audienceElems = document.querySelectorAll('[data-audience-block] [data-widget], [data-ph-widget-id]');
        for (var auEl = 0; auEl < audienceElems.length; auEl++) {
            phApp.audience_state && audienceElems[auEl].setAttribute('data-event-audience', phApp.audience_state);
            phApp.pxPageState && audienceElems[auEl].setAttribute('data-event-pxpagestate', phApp.pxPageState);
            phApp.pxSegmentState && audienceElems[auEl].setAttribute('data-event-pxsegmentstate', phApp.pxSegmentState);
            phApp.pxstate && audienceElems[auEl].setAttribute('data-event-pxstate', phApp.pxstate);
        }
    }

    function loadWidgets(selector, lazyLoad = false) {
        var wdgts = document.querySelectorAll(selector);
        var wdgtsLen = wdgts.length;
        for (var i = 0; i < wdgtsLen; i++) {
            var wdgt = wdgts[i];
            var ignoreIntersection = wdgt && wdgt.getAttribute('data-ignore-lazy-intersection');
            // var isVideoAvailable = wdgt && isVideoExist(wdgt);
            if (wdgt && isInterSectionSupports && phApp.env != 'editor' && !ignoreIntersection) {
                var asLitTmpl = wdgt.getAttribute('as-lit-tmpl');
                var dataWidget = wdgt.getAttribute('data-widget') || '';
                var widgets = [
                    'ph-global-search-v1',
                    'ph-global-search-v3',
                    'ph-cookie-popup-v2',
                    'ph-find-your-fit-container-v1',
                    'ph-cvd-v1',
                    'ph-generic-apply-v1'
                ];
                var isOnetrust = wdgt.closest('[ph-module="onetrust"]');
                var isGenericApply = dataWidget == 'ph-generic-apply-v1';
                if (!asLitTmpl && !isOnetrust && !isGenericApply) {
                    asLitTmpl = wdgt.querySelector('[as-lit-tmpl]');
                    if (!asLitTmpl) {
                        var dataWidget = wdgt.getAttribute('data-widget');
                        if (widgetsIgnoreList.indexOf(dataWidget) != -1) {
                            wdgt.setAttribute('data-ignore-widget-impression', true);
                        }
                        observeElem(wdgt);
                    } else {
                        parentWidgetMap[(wdgt.getAttribute('as-lit-tmpl'), wdgt)];
                    }
                }
                if (
                    !isCrawlerUserAgent() &&
                    widgets.indexOf(dataWidget) != -1 &&
                    (wdgt.hasAttribute('as-lit-tmpl') || isOnetrust || isGenericApply)
                ) {
                    wdgt.removeAttribute('as-lit-tmpl');
                    var isGlobalSearch = ['ph-global-search-v1', 'ph-global-search-v3'].indexOf(dataWidget) != -1;
                    if (isGlobalSearch) {
                        var wgt = wdgt.parentElement && wdgt.parentElement.closest('[data-widget]');
                        wdgt = wgt || wdgt;
                    }
                    wdgt.parentElement.closest('[data-widget]');
                    setTimeForWidget(wdgt, lazyLoad);
                }
            } else {
                enhanceElem(wdgt, lazyLoad);
            }
        }
        revertFooterVisibility();
    }

    function setTimeForWidget(wdgt, lazyLoad = false) {
        setTimeout(function () {
            enhanceElem(wdgt, lazyLoad);
        }, 500);
    }

    function initiatePageState() {
        if (phApp && phApp.phb && phApp.phb.eventAggregator && phApp.phb.eventAggregator.subscribe) {
            phApp.phb.eventAggregator.subscribe('pageState', function (p) {
                if (p) {
                    handlePageState(p.pageState);
                }
            });
        }
        handlePageState();
    }

    function handlePageState(pageState) {
        var state = (phApp && phApp.pageState) || pageState;
        if (state) {
            var stateElems = document.querySelectorAll('[ph-page-state]');
            for (var ies = 0; ies < stateElems.length; ies++) {
                var stateName = stateElems[ies].getAttribute('ph-page-state');
                if (state != stateName && DS_NON_DS_VS_PAGE_STATE_MAP[state] != stateName) {
                    stateElems[ies].parentElement.removeChild(stateElems[ies]);
                } else if (state) {
                    stateElems[ies].classList.remove('hide');
                }
            }
            return;
        }
    }

    function revertFooterVisibility() {
        // To avoid showing the footer with broken styles
        // var footerElem = document.querySelector('.ph-footer');
        //     footerElem && (footerElem.style.visibility = 'visible');
    }

    function loadSpecialElements(elements, lazyLoad = false) {
        elements = elements || splElements;
        for (var i = 0; i < elements.length; i++) {
            var splElemTag = elements[i];
            if (splElemTag) {
                var splElem = document.querySelector('[as-element="' + splElemTag + '"]');
                if (splElem) {
                    enhanceElem(splElem, lazyLoad);
                }
            }
        }
    }

    function enhanceElem(elem, lazyLoad = false) {
        var au = lazyLoad ? window.lazyAurelia : window.localAurelia;
        if (!lazyLoad) {
            const eagerLoadViews = Object.keys(phApp.pageViews || {});
            const widgetView = elem.getAttribute('data-widget') + '-' + (elem.getAttribute('original-view') || '');
            if (eagerLoadViews.indexOf(widgetView) !== -1) {
                return;
            }
        }
        try {

            if (isElementEnhace(elem)) {
                templatingEngine.enhance({
                    container: au.container,
                    element: elem,
                    resources: au.resources
                });
            }
        } catch (error) {
            console.error('Error occured while enhancing element: ', error);
        }
    }

    function isCrawlerUserAgent() {
        var userAgent = window.navigator.userAgent;
        var status = false;
        var crawlerUserAgents = getSiteSettings('crawlerUserAgents');
        if (crawlerUserAgents) {
            var pattern = new RegExp(crawlerUserAgents, 'i');
            status = pattern.test(userAgent.toLowerCase());
        }
        return status;
    }

    function getSiteSettings(key) {
        var ddo = phApp.ddo;
        var siteConfig = ddo && ddo.siteConfig;
        if (siteConfig && siteConfig.data) {
            if (key) {
                return (siteConfig.data.siteSettings && siteConfig.data.siteSettings[key]) || siteConfig.data[key];
            }
            return;
        }
        return siteConfig;
    }

    function isElementEnhace(elem) {
        var isSliderWidget, nestedWdgt;
        try {
            nestedWdgt = elem.parentElement && elem.parentElement.closest('[ph-card-slider-v1], [ph-media-gallery-v1]');
            if (nestedWdgt) {
                isSliderWidget = true;
            }
        } catch (e) { }
        return (
            elem &&
            !elem.au &&
            !elem.getAttribute('as-bridged') &&
            !elem.querySelector('[data-ph-card-slider-v1]') &&
            !elem.querySelector('.au-target') &&
            !isSliderWidget
        );
    }

    function handleLoadWidget(evt) {
        if (evt.target) {
            var widgetTag = evt.target.getAttribute('phae');
            var actionType = evt.target.getAttribute('phae-type');
            var dataPhId = evt.target.getAttribute('data-ph-id');
            var wdgtElem = evt.target.closest('[instance-id]');
            var instanceId = wdgtElem && wdgtElem.getAttribute('instance-id');

            if (!widgetTag) {
                var tagRefEle = evt.target.closest('[phae]');
                widgetTag = tagRefEle.getAttribute('phae');
                dataPhId = tagRefEle.getAttribute('data-ph-id');
                if (widgetTag) {
                    actionType = tagRefEle.getAttribute('phae-type');
                }
            }
            actionType = actionType || 'focus';
            evt.target.removeEventListener(actionType, handleLoadWidget);
            if (templatingEngine) {
                actionAfterLoad = {
                    dataPhId: dataPhId,
                    actionType: actionType
                };
                var selector = '[instance-id="' + instanceId + '"]';
                var elemToEnhance = phVdom.querySelector(selector);
                if (!elemToEnhance) {
                    selector = '[instance-id="' + widgetTag + '"]';
                    elemToEnhance = phVdom.querySelector(selector);
                }
                if (!elemToEnhance) {
                    selector = '[as-element="' + widgetTag + '"]';
                }
                elemToEnhance = phVdom.querySelector(selector);
                if (elemToEnhance && !elemToEnhance.au) {
                    swapAsElement('as-element-silent', elemToEnhance);
                    if (parentWidgetMap[selector]) {
                        elemToEnhance = parentWidgetMap[selector];
                    }
                    enhanceElem(elemToEnhance);
                    setTimeout(function () {
                        var elemToPatch = document.querySelector(selector);
                        elemToPatch.parentElement.replaceChild(elemToEnhance, elemToPatch);
                        applyActionAfterLoad(elemToEnhance);
                    }, 10);
                }
            }
        }
    }

    function applyActionAfterLoad(elemToEnhance) {
        if (actionAfterLoad) {
            var dataPhId = actionAfterLoad.dataPhId;
            var actionType = actionAfterLoad.actionType;
            if (dataPhId) {
                var selector = '[data-ph-id="' + dataPhId + '"]';
                var actionableElem = elemToEnhance.querySelector(selector);
                if (actionableElem) {
                    switch (actionType) {
                        case 'focus':
                            setTimeout(function () {
                                actionableElem.focus();
                            }, 240);
                            break;
                        case 'click':
                            actionableElem.click();
                            setTimeout(function () {
                                if (actionableElem.classList.contains('au-target')) {
                                    actionableElem.focus();
                                }
                            }, 240);
                            break;
                        default:
                            break;
                    }
                }
            }
            actionAfterLoad = undefined;
        }
    }

    function isVideoExist(elem) {
        return elem.querySelector('[ph-video-v1]');
    }

    function loadLazyImages() {
        var lazyImgTags = document.querySelectorAll('[ph-data-src]');
        var lazyImgTagsLen = lazyImgTags.length;
        for (var i = 0; i < lazyImgTagsLen; i++) {
            var lazyImgTag = lazyImgTags[i];
            var phSrc = lazyImgTag.getAttribute('ph-src');
            if (phSrc) {
                var phSrcValue = getImageUrl(phSrc);
                lazyImgTag.removeAttribute('ph-src');
                lazyImgTag.setAttribute('src', phSrcValue);
            } else {
                lazyImgTag.setAttribute('src', lazyImgTag.getAttribute('ph-data-src'));
            }
            lazyImgTag.removeAttribute('ph-data-src');
        }
    }

    function getImageUrl(e) {
        var t = this;
        if (e && -1 != e.indexOf('://')) return e;
        var i = ['cdnUrl', 'refNum', 'locale', 'deviceType'],
            o = '';
        return (
            i.forEach(function (e, i) {
                var n = getParam(e);
                n && n.trim().length > 0 && ((o += n), '/' !== n[n.length - 1] && (o += '/'));
            }),
            o + e
        );
    }

    function getParam(e) {
        return this.phApp[e];
    }

    function handleSliders() {
        var sliderTags = document.querySelectorAll('[ph-card-slider-v1]');
        var sliderTagsLen = sliderTags.length;
        for (var i = 0; i < sliderTagsLen; i++) {
            var sliderTag = sliderTags[i];
            if (sliderTag && !sliderTag.au) {
                var listCards = sliderTag.querySelectorAll('.ph-card');
                for (var eachCard = 0; eachCard < listCards.length; eachCard++) {
                    listCards[eachCard].removeAttribute('role');
                }
            }
        }
    }

    function setResetHeaderWidgets() {
        var widgetTags = document.querySelectorAll('.ph-header [data-widget]:not([type="static"])');
        var widgetTagsLen = widgetTags.length;
        for (var i = 0; i < widgetTagsLen; i++) {
            var widgetTag = widgetTags[i];
            if (!widgetTag.hasAttribute('data-as-element')) {
                var widgeName = widgetTag.getAttribute('as-element');
                widgetTag.setAttribute('data-as-element', widgeName);
                widgetTag.removeAttribute('as-element');
            } else {
                var widgeName = widgetTag.getAttribute('data-as-element');
                widgetTag.setAttribute('as-element', widgeName);
                widgetTag.removeAttribute('data-as-element');
            }
        }
    }

    function loadHeaderWidgets(lazyLoad = false) {
        var widgetTag = document.querySelector('.ph-header > [as-element]');
        widgetTag && enhanceElem(widgetTag, lazyLoad);

        setResetHeaderWidgets();

        var widgetTags = document.querySelectorAll('.ph-header [as-element]:not([type="static"])');
        var widgetTagsLen = widgetTags.length;
        for (var i = 0; i < widgetTagsLen; i++) {
            var widgetTag = widgetTags[i];
            if (widgetTag && !widgetTag.au) {
                triggerEnhanceWithTimer(widgetTag, i, lazyLoad);
            }
        }
    }

    function triggerEnhanceWithTimer(widgetTag, i, lazyLoad = false) {
        setTimeout(
            function () {
                enhanceElem(widgetTag, lazyLoad);
            },
            10 * (i + 1)
        );
    }

    function lazyLoad() {
        if (isInterSectionSupports) {
            lazyObserver = new IntersectionObserver(
                function (entries, observer) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting) {
                            var lazyElem = entry.target;
                            var asLitTmpl = lazyElem.getAttribute('as-lit-tmpl');
                            if (!asLitTmpl) {
                                enhanceElem(lazyElem, true);
                            }
                            lazyObserver.unobserve(lazyElem);
                        }
                    });
                },
                { rootMargin: '0px 0px 30px 0px' }
            );
        }
    }

    function handleStickyElem() {
        var stickyElem = document.querySelector('[ph-sticky]');
        if (stickyElem) {
            document.addEventListener('scroll', initiateScrollSticky.bind(this, stickyElem));
            window.addEventListener('resize', checkIfRealResize.bind(this, stickyElem));
        }
    }

    function checkIfRealResize() {
        if (window.innerWidth !== document.documentElement.clientWidth) {
            setBodyHeight();
        }
    }

    var nextElementSibling;
    function initiateScrollSticky(element) {
        var e = element.offsetTop || 0;
        element.offsetTop || (e = (element.offsetParent && element.offsetParent.offsetTop) || 0),
            element && window.pageYOffset > e
                ? element.classList.contains('ph-sticky-block-fixed') ||
                ((this.currentStickyHeight = element.offsetHeight),
                    element.classList.add('ph-sticky-block-fixed'),
                    setBodyHeight(element, !0))
                : (element.classList.remove('ph-sticky-block-fixed'),
                    (element.style.top = null),
                    nextElementSibling &&
                    nextElementSibling.style &&
                    nextElementSibling.style.paddingTop &&
                    (nextElementSibling.style.paddingTop = null));
    }

    function setBodyHeight(element, e) {
        if (element.classList.contains('ph-sticky-block-fixed') || e) {
            var t = fetchPosition(element);
            if ((t && (element.style.top = t + 'px'), !nextElementSibling)) {
                var i = element;
                for (nextElementSibling = i.nextElementSibling; i && 'BODY' != i.nodeName && !nextElementSibling;)
                    (i = i.parentElement), (nextElementSibling = i && i.nextElementSibling);
            }
            nextElementSibling && (nextElementSibling.style.paddingTop = element.offsetHeight + t + 'px');
        }
    }

    function fetchPosition(element) {
        for (
            var e = document.querySelectorAll('.pcs-sticky-header, .ph-sticky-header, .ph-sticky-block-fixed,.phw-sticky-top-all'),
            t = 0,
            i = 0;
            i < e.length;
            i++
        )
            element !== e[i] && (t += e[i].offsetHeight);
        return t;
    }

    function observeElem(elem) {
        lazyObserver.observe(elem);
    }

    function elementClosestPolyfill() {
        if (!Element.prototype.matches) {
            Element.prototype.matches = Element.prototype.msMatchesSelector || Element.prototype.webkitMatchesSelector;
        }

        if (!Element.prototype.closest) {
            Element.prototype.closest = function (s) {
                var el = this;

                do {
                    if (Element.prototype.matches.call(el, s)) return el;
                    el = el.parentElement || el.parentNode;
                } while (el !== null && el.nodeType === 1);
                return null;
            };
        }
    }

    function loadRecomWidget() {
        loadSpecialElements(recomWidget);
        document.removeEventListener('getUserProfileData', loadRecomWidget);
    }

    function getDDOFromCache(ddoKey) {
        const ddo = phApp.ddo;
        const pageGroup = phApp.pageGroup || {};
        return ddo[ddoKey] || pageGroup[ddoKey];
    }

    function fetchCachedDdo(ddoKey) {
        const ddoResponse = getDDOFromCache(ddoKey);
        let resp;
        if (ddoResponse) {
            resp = {
                [ddoKey]: ddoResponse
            };
        }
        return resp;
    }

    function formatParams(params) {
        return Object
            .keys(params)
            .map(function (key) {
                return key + "=" + encodeURIComponent(params[key])
            })
            .join("&")
    }

    function prepareCdnRequestUrl(cdnInfo, ddoKey, reqObj) {
        const isGloballyManaged = (cdnInfo.globallyManagedDdos || []).indexOf(ddoKey) !== -1;
        let url;

        if (isGloballyManaged) {
            // Format: /api/ddo/{ddoKey}?refNum={refNum}&locale={locale}&siteType={siteType}&deviceType={deviceType}
            url = `${cdnInfo.cdnUrl}/api/ddo/${ddoKey}?refNum=${getParam('refNum')}&locale=${getParam('locale')}&siteType=${getParam('siteType')}&deviceType=${getParam('deviceType')}`;
        } else {
            // Format: /api/{refNum}/{ddoKey}?locale={locale}&siteType={siteType}&deviceType={deviceType}
            url = `${cdnInfo.cdnUrl}/api/${getParam('refNum')}/${ddoKey}?locale=${getParam('locale')}&siteType=${getParam('siteType')}&deviceType=${getParam('deviceType')}`;
        }

        // Add page-specific parameters for all DDOs
        if ((cdnInfo.pageNameLevelDdos || []).indexOf(ddoKey) !== -1) {
            url += '&pageName=' + getParam('pageName');
        } else if ((cdnInfo.pageIdlevelDdos || []).indexOf(ddoKey) !== -1) {
            url += '&pageId=' + getParam('pageId');
        }

        // Add request object parameters for all DDOs
        if (reqObj && Object.keys(reqObj).length > 0) {
            url += '&' + formatParams(reqObj);
        }

        return url;
    }

    function fetchDdoActual(ddoKey, params, lowPriority = false) {
        return new Promise((resolve, _reject) => {
            const cdnInfo = getSiteSettings('cdnConfig') || {};
            const iscdnEnabled = getSiteSettings('iscdnEnabled');

            const ddoResponse = fetchCachedDdo(ddoKey);
            if (ddoResponse) {
                resolve(ddoResponse);
            } else if (iscdnEnabled && cdnInfo.cdnDdos && cdnInfo.cdnDdos.indexOf(ddoKey) != -1) {
                let payload;
                if (params && Object.keys(params).length) {
                    try {
                        payload = JSON.stringify(params);
                    } catch (e) { }
                }
                const reqObj = {};
                if (payload) {
                    reqObj.payload = payload;
                }
                
                const url = prepareCdnRequestUrl(cdnInfo, ddoKey, reqObj);
                fetchGetRequest(url, lowPriority).then((resp) => {
                    resolve(resp);
                    setEagerLoadAndResolvePromise(resp, ddoKey, params);
                });
            } else {
                params = params || {};
                params.ddoKey = ddoKey;
                fetchData(params, lowPriority).then((resp) => {
                    resolve(resp);
                    setEagerLoadAndResolvePromise(resp, ddoKey, params);
                });
            }
        });
    }

    function fetchGetRequest(url, lowPriority = false) {
        const myHeaders = new Headers();
        const myRequest = new Request(url, {
            method: 'GET',
            headers: myHeaders,
            mode: 'cors',
            cache: 'default'
        });
        return fetch(myRequest, {
            priority: lowPriority ? 'low' : 'high'
        }).then((response) => {
            if (response.headers.get('Content-Type').indexOf('text/html') === -1) {
                return response.json();
            } else {
                return response.text();
            }
        });
    }

    function getWidgetApiEndpoint() {
        return phApp.widgetApiEndpoint;
    }

    function getCommonParams() {
        const params = {
            lang: phApp.locale,
            deviceType: phApp.deviceType,
            country: phApp.country,
            pageName: phApp.pageName,
            pageId: phApp.pageId,
        };
        return params;
    }

    function getCsrfToken() {
        let csrfTokenDocEle = document.getElementById(CSRF_TOKEN);
        phApp.csrfToken = (csrfTokenDocEle && csrfTokenDocEle.innerText) || '';
        if (!phApp.csrfToken) {
            phApp.csrfToken = phApp.sessionParams && phApp.sessionParams.csrfToken;
        }
        return phApp.csrfToken;
    }

    function fetchData(payload, lowPriority = false) {
        const widgetApiEndpoint = getWidgetApiEndpoint();
        const commonParams = getCommonParams() || {};
        const csrf = getCsrfToken();
        const params = { ...commonParams, ...(payload || {}) };
        return fetch(widgetApiEndpoint, {
            method: 'post',
            credentials: 'include',
            headers: {
                'X-CSRF-TOKEN': csrf,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params || {}),
            priority: lowPriority ? 'low' : 'high'
        }).then((response) => response.json());
    }

    function setEagerLoadAndResolvePromise(response, ddoKey, params) {
        params = params || {};
        if (configuredMakeEagerLoadDdos.indexOf(ddoKey) !== -1 || params.isEagerLoad) {
            isDdoEagerLoaded[ddoKey].forEach((promise) => {
                promise.resolve(response);
            });
            delete isDdoEagerLoaded[ddoKey];
        }
    }

    function fetchDdo(ddoKey, params, lowPriority = false) {
        params = params || {};
        const ddo = fetchCachedDdo(ddoKey);
        if (isDdoEagerLoaded.hasOwnProperty(ddoKey) && !ddo) {
            const dfd = {
                promise: new Promise((_resolve, _reject) => { })
            };
            isDdoEagerLoaded[ddoKey].push(dfd);
            return dfd.promise;
        } else {
            if ((configuredMakeEagerLoadDdos.indexOf(ddoKey) !== -1 || params.isEagerLoad) && !ddo) {
                isDdoEagerLoaded[ddoKey] = [];
            }
            return fetchDdoActual(ddoKey, params, lowPriority);
        }
    }

    function createWidgetCntr(data, v) {
        const hed = document.querySelector('head');
        const scr = document.createElement('script');
        const theme = document.createElement('style');
        if (hed) {
            const widgetId = v.scriptName + '-' + v.viewName + '-' + v.themeName;
            scr.setAttribute('type', 'text/x-ph-tmpl');
            scr.setAttribute('id', widgetId);
            scr.innerHTML = data.html;
            hed.appendChild(scr);

            if (data.theme) {
                theme.setAttribute('type', 'text/css');
                theme.setAttribute('id', widgetId);
                theme.innerHTML = data.theme;
                hed.appendChild(theme);
            }
        }
    }

    function setEagerLoadDDOs() {
        const eagerLoadDDOs = getSiteSettings('configuredMakeEagerLoadDdos') || [];
        if (eagerLoadDDOs.length) {
            eagerLoadDDOs.forEach((ddoName) => {
                if (configuredMakeEagerLoadDdos.indexOf(ddoName) === -1) {
                    configuredMakeEagerLoadDdos.push(ddoName);
                }
            });
        }
    }

    function getWidgetVersionsFromStorage() {
        try {
            const storedData = localStorage.getItem(WIDGET_VERSIONS_STORAGE_KEY);
            if (storedData) {
                const parsedData = JSON.parse(storedData);
                // Check if data is less than 1 hour old
                const oneHour = 60 * 60 * 1000;
                if (parsedData.timestamp && (Date.now() - parsedData.timestamp) < oneHour) {
                    return parsedData.versions;
                }
            }
        } catch (err) {
            console.error('Error reading widget versions from localStorage:', err);
        }
        return null;
    }

    function saveWidgetVersionsToStorage(versions) {
        try {
            const dataToStore = {
                versions: versions,
                timestamp: Date.now()
            };
            localStorage.setItem(WIDGET_VERSIONS_STORAGE_KEY, JSON.stringify(dataToStore));
        } catch (err) {
            console.error('Error saving widget versions to localStorage:', err);
        }
    }

    function getContentStorageKey() {
        const siteType = phApp.siteType;
        const locale = phApp.locale;
        const pageId = phApp.pageId;
        
        // Only use localStorage if all required values are available
        if (!siteType || !locale || !pageId) {
            return null;
        }
        
        return `${CONTENT_STORAGE_KEY_PREFIX}${siteType}_${locale}_${pageId}`;
    }

    function getContentFromStorage() {
        try {
            const storageKey = getContentStorageKey();
            if (!storageKey) {
                return null; // Skip localStorage if key cannot be generated
            }
            
            const storedData = localStorage.getItem(storageKey);
            if (storedData) {
                const parsedData = JSON.parse(storedData);
                // Check if data is less than 1 hour old
                const oneHour = 60 * 60 * 1000;
                if (parsedData.timestamp && (Date.now() - parsedData.timestamp) < oneHour) {
                    return parsedData.content;
                }
            }
        } catch (err) {
            console.error('Error reading content from localStorage:', err);
        }
        return null;
    }

    function saveContentToStorage(content) {
        try {
            const storageKey = getContentStorageKey();
            if (!storageKey) {
                return; // Skip localStorage if key cannot be generated
            }
            
            const dataToStore = {
                content: content,
                timestamp: Date.now()
            };
            localStorage.setItem(storageKey, JSON.stringify(dataToStore));
        } catch (err) {
            console.error('Error saving content to localStorage:', err);
        }
    }

    function getTranslationsStorageKey() {
        const siteType = phApp.siteType;
        const locale = phApp.locale;
        const pageId = phApp.pageId;
        
        // Only use localStorage if all required values are available
        if (!siteType || !locale || !pageId) {
            return null;
        }
        
        return `${TRANSLATIONS_STORAGE_KEY_PREFIX}${siteType}_${locale}_${pageId}`;
    }

    function getTranslationsFromStorage() {
        try {
            const storageKey = getTranslationsStorageKey();
            if (!storageKey) {
                return null; // Skip localStorage if key cannot be generated
            }
            
            const storedData = localStorage.getItem(storageKey);
            if (storedData) {
                const parsedData = JSON.parse(storedData);
                // Check if data is less than 1 hour old
                const oneHour = 60 * 60 * 1000;
                if (parsedData.timestamp && (Date.now() - parsedData.timestamp) < oneHour) {
                    return parsedData.translations;
                }
            }
        } catch (err) {
            console.error('Error reading translations from localStorage:', err);
        }
        return null;
    }

    function saveTranslationsToStorage(translations) {
        try {
            const storageKey = getTranslationsStorageKey();
            if (!storageKey) {
                return; // Skip localStorage if key cannot be generated
            }
            
            const dataToStore = {
                translations: translations,
                timestamp: Date.now()
            };
            localStorage.setItem(storageKey, JSON.stringify(dataToStore));
        } catch (err) {
            console.error('Error saving translations to localStorage:', err);
        }
    }

    async function fetchWidgetVersionsFromAPI(lowPriority = false) {
        try {
            return fetchDdo(DDO_KEY_GET_WIDGET_VERSIONS, {}, lowPriority).then((widgetVersionsRes) => {
                widgetVersionsRes = widgetVersionsRes[DDO_KEY_GET_WIDGET_VERSIONS] || {};
                if (widgetVersionsRes && widgetVersionsRes.status == 'success') {
                    return widgetVersionsRes.data || {};
                }
                return {};
            });
        } catch (err) {
            console.error(`Exception occurred while fetching widget versions: ${err}`);
            return {};
        }
    }

    async function fetchContentFromAPI(lowPriority = false) {
        try {
            const dynamicWidgetData = getDynamicWidgetData();
            const fetchContentReq = prepareFetchContentRequest(dynamicWidgetData);

            let res = await fetchDdo(NON_DS_CONTENT_FETCH_DDO_KEY, fetchContentReq, lowPriority);
            res = res[NON_DS_CONTENT_FETCH_DDO_KEY];
            if (res && res.status === 'success' && res.data) {
                let { content, bindables } = splitContentAndBindables(res.data.contentData);
                content = moveWidgetContentToRoot(content);
                return {
                    content: content,
                    bindables: bindables,
                    designData: res.data.designData
                };
            }
            return null;
        } catch (error) {
            console.error('Error occurred while fetching content from API:', error);
            return null;
        }
    }

    async function getTranslationsFromAPI(lowPriority = false) {
        try {
            if (phApp.env === 'editor') {
                return null;
            }

            const payload = [];
            document.querySelectorAll(AURELIA_DYNAMIC_WIDGET_SELECTOR).forEach((elem) => {
                const widgetTag = elem.getAttribute('as-element');
                const instanceId = elem.getAttribute('instance-id');
                const view = elem.getAttribute('original-view') || 'default';
                payload.push({ widgetTag, view, instanceId });
            });

            const res = await fetchDdo('canvasGetWidgetTranslations', { data: payload }, lowPriority);
            if (res && res.canvasGetWidgetTranslations) {
                const translations = res.canvasGetWidgetTranslations;
                if (translations) {
                    return translations.data;
                }
            }
            return null;
        } catch (error) {
            console.error('Error occurred while fetching translations from API:', error);
            return null;
        }
    }

    async function fetchWidgetVersions() {
        try {
            // First, try to get from localStorage
            const cachedVersions = getWidgetVersionsFromStorage();
            if (cachedVersions) {
                // Update localStorage asynchronously in background
                fetchWidgetVersionsFromAPI(true).then((freshVersions) => {
                    if (freshVersions && Object.keys(freshVersions).length > 0) {
                        saveWidgetVersionsToStorage(freshVersions);
                    }
                }).catch((err) => {
                    console.error('Background widget versions update failed:', err);
                });
                return cachedVersions;
            }

            // If not in localStorage, fetch from API and cache
            const versions = await fetchWidgetVersionsFromAPI();
            if (versions && Object.keys(versions).length > 0) {
                saveWidgetVersionsToStorage(versions);
            }
            return versions;
        } catch (err) {
            console.error(`Exception occurred while fetching widget versions: ${err}`);
            return {};
        }
    }

    function fetchUnEnhancedAuWidgets() {
        const unEnhancedAuWdgtEle = document.querySelectorAll(UN_ENHANCED_AURELIA_WIDGET_SELECTOR);

        const unEnhancedAuWdgts = [];
        for (let i = 0; i < unEnhancedAuWdgtEle.length; ++i) {
            const dynamicWidget = unEnhancedAuWdgtEle[i];

            const originalView = dynamicWidget.getAttribute('original-view');
            const tagName = dynamicWidget.getAttribute('as-element');

            const dynamicWidgetId = [tagName, originalView].join('-');
            dynamicWidget.setAttribute('data-tag-name', dynamicWidgetId);

            const instanceId = dynamicWidget.getAttribute('instance-id');

            if (instanceId) {
                unEnhancedAuWdgts.push(dynamicWidgetId);
            }
        }

        return unEnhancedAuWdgts;
    }

    async function fetchAuWidgetData(widgetVersions, widgetIds) {
        const getWidgetDataReq = {
            widgetIds: widgetIds,
            ddoKey: NON_DSD_GLOBAL_VIEWS_DDO_KEY
        };

        try {
            const res = await fetchDdo(NON_DSD_GLOBAL_VIEWS_DDO_KEY, getWidgetDataReq);
            const widgetsData = res.getWidgetMetaData || {};

            return widgetsData.data ? widgetsData.data.map((x) => x[Object.keys(x)[0]]) : [];
        } catch (err) {
            console.error(err);
            return {};
        }
    }

    async function loadScriptWithRequire(url) {
        return new Promise((resolve, _reject) => {
            require([url], function (x) {
                return resolve(true);
            });
        }).catch((err) => {
            console.error(`Error loading script: ${url} - ${err}`);
            return _reject(false);
        });
    }

    function getComponentNameFromScript(scriptName) {
        var hyphenLastIdx = scriptName.lastIndexOf('-');
        var component = `${scriptName.substring(hyphenLastIdx + 1)}/${scriptName.substring(0, hyphenLastIdx)}`;
        return component;
    }

    function getComponentNameFromWidgetId(widgetId) {
        try {
            const versionMatch = widgetId.match(/-v\d+-/);
            if (versionMatch) {
                const versionStartIdx = versionMatch.index;
                const widgetName = widgetId.substring(0, versionStartIdx);
                const widgetVersionAndViewStr = widgetId.substring(versionStartIdx + 1);
                const wigdetVersionEndIdx = widgetVersionAndViewStr.indexOf('-');
                const wigdetVersion = widgetVersionAndViewStr.substring(0, wigdetVersionEndIdx);
                return `${wigdetVersion}/${widgetName}`;
            } else {
                console.error(`Invalid widget id: ${widgetId}`);
                return '';
            }
        } catch (err) {
            console.error(`Error getting component name from widget id: ${widgetId} - ${err}`);
            return '';
        }
    }

    async function loadAuWidgetsV1(auWidgetsData) {
        const components = new Set();
        const wdgtScrLoadPromises = [];
        for (let i = 0; i < auWidgetsData.length; ++i) {
            const widgetData = auWidgetsData[i];
            createWidgetCntr(widgetData, auWidgetsData[i]);

            if (auWidgetsData[i].script) {
                const component = getComponentNameFromScript(auWidgetsData[i].scriptName);
                wdgtScrLoadPromises.push(
                    loadScriptWithRequire(auWidgetsData[i].script).then((_res) => {
                        components.add(component);
                    })
                );
            }
        }

        return Promise.all(wdgtScrLoadPromises).then(() => {
            return components;
        });
    }

    function getWidgetScriptUrl(widgetVersions, widgetId) {
        try {
            if (widgetId && widgetId.endsWith('-')) {
                widgetId = widgetId + 'default';
            }
            if (widgetVersions[widgetId]) {
                const widgetScriptsConfig = getSiteSettings('widgetScriptsConfig');
                const cdnBaseUrl = widgetScriptsConfig && widgetScriptsConfig.cdnBaseUrl;
                const widgetScriptPath = widgetScriptsConfig && widgetScriptsConfig.widgetScriptPath;
                const widgetScriptUrl = `${cdnBaseUrl}/${widgetScriptPath}/${widgetId}-${widgetVersions[widgetId]}.js`;
                return widgetScriptUrl;
            } else {
                console.error(`Invalid widget id: ${widgetId}`);
                return '';
            }
        } catch (err) {
            console.error(`Error getting widget script url: ${widgetId} - ${err}`);
            return '';
        }
    }

    async function loadAuWidgets(widgetVersions, unEnhancedAuWdgts) {
        const components = new Set();
        const wdgtScrLoadPromises = unEnhancedAuWdgts.map(async (widgetId) => {
            const widgetComponents = await loadWidget(widgetVersions, widgetId);
            widgetComponents.forEach((component) => {
                components.add(component);
            });
        });

        return Promise.all(wdgtScrLoadPromises).then(() => {
            return components;
        });
    }

    async function loadWidget(widgetVersions, widgetId) {
        const widgetScriptUrl = getWidgetScriptUrl(widgetVersions, widgetId);

        const components = new Set();
        if (widgetScriptUrl) {
            await loadScriptWithRequire(widgetScriptUrl);
            const componentName = getComponentNameFromWidgetId(widgetId);
            components.add(componentName);

            const childComponents = await loadChildWidgetsOfLazyLoadedWidget(widgetVersions, widgetId);
            childComponents.forEach((childComponent) => {
                components.add(childComponent);
            });
        }

        return Promise.resolve(components);
    }

    async function loadChildWidgetsOfLazyLoadedWidget(widgetVersions, widgetId) {
        if (phApp.lazyLoadChildData && phApp.lazyLoadChildData[widgetId]) {
            const childComponents = new Set();
            const childWidgetScriptLoadPromises = phApp.lazyLoadChildData[widgetId].map(async (childWidgetId) => {
                const childWidgetScriptUrl = getWidgetScriptUrl(widgetVersions, childWidgetId);
                if (childWidgetScriptUrl) {
                    await loadScriptWithRequire(childWidgetScriptUrl);
                    const childComponentName = getComponentNameFromWidgetId(childWidgetId);
                    childComponents.add(childComponentName);

                    const grandChildComponents = await loadChildWidgetsOfLazyLoadedWidget(widgetVersions, childWidgetId);
                    grandChildComponents.forEach((grandChildComponent) => {
                        childComponents.add(grandChildComponent);
                    });
                    return Promise.resolve(true);
                } else {
                    return Promise.resolve(true);
                }
            });

            return Promise.all(childWidgetScriptLoadPromises).then(() => {
                return childComponents;
            });
        } else {
            return Promise.resolve([]);
        }
    }

    function registerModules(moduleName, modules) {
        define(moduleName, ['require', 'exports'], function (require, exports) {
            'use strict';
            Object.defineProperty(exports, '__esModule', { value: true });
            exports.default = [...modules];
        });
    }

    function createEventBusBridge() { }

    async function lazyLoadWidgets() {
        const unEnhancedAuWdgts = fetchUnEnhancedAuWidgets();
        if (unEnhancedAuWdgts && unEnhancedAuWdgts.length > 0) {
            const widgetVersions = await fetchWidgetVersions();
            // const lazyLoadWidgetData = await fetchAuWidgetData(widgetVersions, unEnhancedAuWdgts)
            const components = await loadAuWidgets(widgetVersions, unEnhancedAuWdgts);
            registerModules('lazy-components', components);
        } else {
            registerModules('lazy-components', []);
        }
    }

    function getTranslations() {
        if (phApp.env === 'editor') {
            return;
        }

        try {
            // First, try to get from localStorage
            const cachedTranslations = getTranslationsFromStorage();
            if (cachedTranslations) {
                // Apply cached translations immediately
                phApp.translations = phApp.translations || {};
                phApp.translations = cachedTranslations;

                // Update localStorage asynchronously in background
                getTranslationsFromAPI(true).then((freshTranslations) => {
                    if (freshTranslations) {
                        saveTranslationsToStorage(freshTranslations);
                        // Also update the current translations with fresh data
                        phApp.translations = freshTranslations;
                    }
                }).catch((err) => {
                    console.error('Background translations update failed:', err);
                });
                return;
            }

            // If not in localStorage, fetch from API and cache
            getTranslationsFromAPI().then((translationsData) => {
                if (translationsData) {
                    // Apply translations to global store
                    phApp.translations = phApp.translations || {};
                    phApp.translations = translationsData;

                    // Save to localStorage for next time
                    saveTranslationsToStorage(translationsData);
                }
            }).catch((error) => {
                console.error('Error occurred while fetching translations:', error);
            });
        } catch (error) {
            console.error('Error occurred while getting translations:', error);
        }
    }

    function setDataFuncWidgetId() {
        document.querySelectorAll('section [data-func-widget-id]').forEach((elem) => {
            const dataFuncWidgetId = elem.getAttribute('data-func-widget-id');
            if (dataFuncWidgetId && dataFuncWidgetId.startsWith('ph-') && elem.parentElement) {
                elem.parentElement.setAttribute('data-func-widget-id', dataFuncWidgetId);
            }
        });
    }

    function getSettingsIdentifiersFileUrl() {
        try {
            const settingsIdentifiersFileUrl =
                getSiteSettings('settingsIdentifiersFileUrl') ||
                'https://assetsqa.phenompro.com/CareerConnectResources/siteqa1/common/js/vendor/classesForCms.js?v=' +
                    Date.now()
            return settingsIdentifiersFileUrl
        } catch (err) {
            console.error('Error getting settings identifiers file url:', err);
            return '';
        }
    }

    function loadFileForCMSSetting() {
        const script = document.createElement('script');
        const link = getSettingsIdentifiersFileUrl();
        script.src = link;
        document.head.appendChild(script);
    }

    function injectStylesForLinksInPpcContent() {
        try {
            const injectStylesForLinksInPpcContent = getSiteSettings('injectStylesForLinksInPpcContent');
            if(injectStylesForLinksInPpcContent) {
                const style = document.createElement('style');
                style.innerHTML = `
                    ppc-content a.cke-link:focus, ppc-content a.cke-link:hover, ppc-content a.cke-link, ppc-content a[data-cke-saved-href]:focus, ppc-content a[data-cke-saved-href]:hover, ppc-content a[data-cke-saved-href] {
                        font-weight: inherit !important;
                        color: inherit !important;
                        background-color: inherit !important;
                        text-decoration: inherit;
                    }
                `;
                style.setAttribute('ph-style-id', 'ph-ppc-content-link-styles');
                document.head.appendChild(style);
            }
        } catch (e) {
            console.error('Error while injecting styles for links in PPC content', e);
        }
    }

    function init() {
        document.body.removeAttribute('aurelia-app');
        elementClosestPolyfill();
        lazyLoad();
        fetchDOM();
        attachEventListeners();
        setEagerLoadDDOs();
        setDataFuncWidgetId();
        loadFileForCMSSetting();
        getTranslations();
        // setTimeout(function () {
        //     loadFramework();
        // }, 50)
        lazyLoadWidgets().then(() => {
            loadFramework(true);
            setTimeout(function () {
                createEventBusBridge();
            }, 50);
        });
        injectStylesForLinksInPpcContent();
    }

    return {
        init: init,
        loadFramework: loadFramework
    };
}

window.phEnhancer = new PhEnhancer();
if (window.P) {
    P.config({
        longStackTraces: !1,
        warnings: {
            wForgottenReturn: !1
        }
    });
}

if (phApp.siteType !== 'internal') {
    phEnhancer.init();
} else {
    document.body.removeAttribute('aurelia-app');
    phEnhancer.loadFramework();
}