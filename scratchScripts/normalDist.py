import matplotlib.pyplot as plt
import numpy as np

## The Normal Distribution ##
mean, sigma = -3, 0.5 # mean and standard deviation
s = 10**np.random.normal(mean, sigma, 4000)
print(s[0:10])
abs(mean - np.mean(s))
abs(sigma - np.std(s, ddof=1))

count, bins, ignored = plt.hist(s, 30, density=True)
# plt.plot(bins, 1/(sigma * np.sqrt(2 * np.pi)) *
#                np.exp( - (bins - mean)**2 / (2 * sigma**2) ),
#          linewidth=2, color='r')

plt.show()

# ## The lognormal Distribution ##
# mu, sigma = 0.0001, 0.5 # mean and standard deviation
# s = np.random.lognormal(mu, sigma, 1000)

# count, bins, ignored = plt.hist(s, 100, density=True, align='mid')

# x = np.linspace(min(bins), max(bins), 10000)
# pdf = (np.exp(-(np.log(x) - mu)**2 / (2 * sigma**2))
#        / (x * sigma * np.sqrt(2 * np.pi)))


# plt.plot(x, pdf, linewidth=2, color='r')
# plt.axis('tight')
# plt.show()