# This is going to be a wonderful test!

### * First test

### ** Random data

# We generate some random data with a long text before so that the text in the
# input file is broken over several lines
x = sin(rnorm(1000)) ^ 2
y = rnorm(1000) + x

### ** Analysis 

# Let's load a library
library(MASS)
# And now let's calculate some 2D density map:
z = kde2d(x, y, n = 128)

### ** Graph

# Time for plotting!
plot(x, y, pch = 21, bg = "lightblue", col = "lightblue",
     cex = 0.5)
contour(z, add = T, col = "darkred", nlevels = 15)

### * Second test

# Well, maybe we can try something else.
x = seq(0, 2 * pi, by = 0.01)
y = sin(x^2)
plot(x, y, type = "l", col = "")

## @end@

### * Third test

# This should NOT be in the output because of the @end@ tag before
x = 1:10
y = sample(x)
plot(x, y)
cor.test(x, y, method = "spearman")
