# Bodies creation README File

## Spacecraft class

### Derivation of "set_distance_from_co_orbiting" function.

The function assumes two spacecraft in a coplanar keplerian orbit. This allows the keplerian elements to be sourced directly from the instance. Additionaly, it is assumed the other spacecraft has a true anomaly of zero, this simplifies the derivations. 

The radius equation for keplerian orbits is defined as:

$$
r = \frac{a(1-e^2)}{1+e\cos\theta}
$$

From this equation we find the cartesian position relative to the orbited body, with x-axis aligned with the periapsis. The position vectors for the reference spacecraft (Subscript 1) and the one the distance is being calculated for (Subscript 2) are:

$$
\vec{r}_1 = \left( \frac{a(1-e^2)}{1+e}, 0\right) \hspace{1cm}
\vec{r}_2 = \left( \frac{a(1-e^2)}{1+e\cos\theta_2}\cdot\cos\theta_2, \frac{a(1-e^2)}{1+e\cos\theta_2}\cdot\sin\theta_2\right)
$$

The distance (D) between these two is the magnitude of the relative position vector $|\vec{r}_2 - \vec{r}_1|$. This magnitude can be rearranged so that the entire equation is rewritten as a quadratic equation with variable $x=\cos\theta_2$. ($ax^2 + bx + c = 0$):

$$
\Phi = \frac{D^2}{(a(1-e^2))^2}-\left(\frac{1}{1+e}\right)^2
$$
$$
a = -2e - \Phi(e^2 + e^3)
$$
$$
b = -2 -\Phi(2e + 2e^2)
$$
$$
c = (1 + e)(1 - \Phi)
$$


The function then solves this quadratic and extracts the required $\theta_2$ required for the desired spacing via $\arccos(x)$. 