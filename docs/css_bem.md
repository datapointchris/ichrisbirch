# CSS BEM

HTML5 semantic elements help structure the content of web pages in a way that is meaningful for both browsers and developers. BEM (Block, Element, Modifier) is a methodology that aims to create reusable components and code sharing in front-end development. It stands for Block, Element, Modifier and provides a way for developers to name their CSS classes in a strict, understandable, and informative way, significantly improving code maintainability and readability.

Here’s an example of a medium complexity page using HTML5 semantic tags combined with BEM CSS naming conventions. This example includes a basic layout with a header, navigation, a main content area with an article and sidebar, and a footer.

## Example HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Example Page with HTML5 and BEM</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>

<header class="header">
    <h1 class="header__title">My Website</h1>
    <nav class="nav">
        <ul class="nav__list">
            <li class="nav__item"><a class="nav__link" href="#home">Home</a></li>
            <li class="nav__item"><a class="nav__link" href="#about">About</a></li>
            <li class="nav__item"><a class="nav__link" href="#contact">Contact</a></li>
        </ul>
    </nav>
</header>

<main class="main">
    <article class="article">
        <h2 class="article__title">Blog Post Title</h2>
        <p class="article__meta">Posted on <time datetime="2023-04-01">April 1, 2023</time></p>
        <div class="article__content">
            <p>This is a blog post. It describes something interesting.</p>
        </div>
    </article>

    <aside class="sidebar">
        <div class="sidebar__section">
            <h2 class="sidebar__title">About Me</h2>
            <p>I am a web developer...</p>
        </div>
        <div class="sidebar__section">
            <h2 class="sidebar__title">Archives</h2>
            <ul class="sidebar__list">
                <li class="sidebar__item">March 2023</li>
                <li class="sidebar__item">February 2023</li>
                <li class="sidebar__item">January 2023</li>
            </ul>
        </div>
    </aside>
</main>

<footer class="footer">
    <p class="footer__text">© 2023 My Website</p>
</footer>

</body>
</html>
```

## Example CSS Using BEM

```css
.header {
    background-color: #f0f0f0;
    padding: 20px 0;
}

.header__title {
    margin: 0;
    padding: 0 20px;
}

.nav {
    background-color: #333;
}

.nav__list {
    list-style: none;
    display: flex;
    justify-content: center;
    padding: 0;
}

.nav__item {
    margin: 0 10px;
}

.nav__link {
    color: white;
    text-decoration: none;
}

.main {
    display: flex;
    margin: 20px;
}

.article {
    flex: 3;
}

.article__title {
    color: #333;
}

.article__meta {
    font-style: italic;
}

.sidebar {
    flex: 1;
    padding-left: 20px;
}

.sidebar__title {
    font-size: 20px;
}

.footer {
    background-color: #333;
    color: white;
    text-align: center;
    padding: 10px 0;
}
```

### BEM Explanation

- **Block**: Standalone entity that is meaningful on its own (e.g., `header`, `nav`, `article`, `sidebar`, `footer`). Blocks can be nested inside each other but should remain independent.

- **Element**: A part of a block that has no standalone meaning and is semantically tied to its block (e.g., `header__title`, `nav__link`, `article__title`). Elements are always part of a block, not another element.

- **Modifier**: Flags on blocks or elements used to change appearance, behavior, or state (e.g., `nav__link--active`, although not shown in the example above, would represent an active state of the navigation link).

BEM's naming convention makes the structure of HTML/CSS clear and understandable at a glance, provides a strong contract for developers on a project, and helps avoid CSS naming conflicts by using unique names based on the block-element hierarchy.
