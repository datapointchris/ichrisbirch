# CSS Notes

## Flex

The display: flex and display: inline-flex properties in CSS are used to create a flex container and make its children flex items. The difference between them lies in how the flex container behaves in relation to other elements.

display: flex: This makes the container a block-level flex container. A block-level element takes up the full width of its parent element, and it starts and ends with a new line. So, a flex container with display: flex will take up the full width of its parent and will not allow other elements to sit next to it on the same line.

display: inline-flex: This makes the container an inline-level flex container. An inline-level element only takes up as much width as it needs, and it does not start or end with a new line. So, a flex container with display: inline-flex will only be as wide as necessary to contain its items, and it will allow other elements to sit next to it on the same line.
