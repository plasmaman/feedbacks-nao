
#from matplotlib.colorbar import ColorbarBase
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import traceback
from datetime import date, datetime, timedelta
import pickle
from scipy import interpolate
import calendar
from matplotlib.colors import ListedColormap
from localsettings import HOMEDIR, DATADIR, PYTHONDIR #, DATALAKEDIR
import sys

DPI = 150
FONTSIZE = 9
REARTH = 6.371e6
TWOCOLUMN_WIDTH_INCHES = 6.5
TWI = TWOCOLUMN_WIDTH_INCHES
ONECOLUMN_WIDTH_INCHES = 3.17
#LETTERS = 'abcdefghijklmnopqrstuvxyzabcdefghijklmnopqrstuvxyz'
CACHEROOT = f'{DATADIR}/cache/python'

C0 = '#1f77b4'
C1 = '#ff7f0e'
C2 = '#2ca02c'
C3 = '#d62728'
C4 = '#9467bd'
C5 = '#8c564b'
C8 = '#bcbd22'
C9 = '#17becf'

monthnames = {m: date(year=2000, month=m, day=1).strftime('%b') for m in range(1,13)}
longmonthnames = {m: date(year=2000, month=m, day=1).strftime('%B') for m in range(1,13)}

def smooth_and_spline(xi_orig, yi_orig, zi_orig, sigma = 1.5):
	from scipy.ndimage import gaussian_filter
	zi_smooth = gaussian_filter(zi_orig, sigma=sigma)
	#plt.contourf(xi, yi, zi_smooth, cv, cmap=cmap, vmin=cv[0], vmax=cv[-1], transform=sub['proj'])
	if not np.all(np.diff(xi_orig[0,:]) > 0):
		xi_orig = np.fliplr(xi_orig)
		zi_smooth = np.fliplr(zi_smooth)
	if not np.all(np.diff(yi_orig[:,0]) > 0):
		yi_orig = np.flipud(yi_orig)
		zi_smooth = np.flipud(zi_smooth)
	from scipy.interpolate import RectBivariateSpline
	xi_new = np.linspace(np.min(xi_orig.ravel()), np.max(xi_orig.ravel()), xi_orig.shape[1]*6)
	yi_new = np.linspace(np.min(yi_orig.ravel()), np.max(yi_orig.ravel()), yi_orig.shape[0]*6)
	spline = RectBivariateSpline(yi_orig[:,0], xi_orig[0,:], zi_smooth)
	zi_new = spline(yi_new, xi_new)
	return xi_new, yi_new, zi_new

def usetex(b):
	rc_fonts = {
	    "text.usetex": b,
	    'mathtext.default': 'regular',
	    'text.latex.preamble': r"\usepackage{bm}",
	}
	matplotlib.rcParams.update(rc_fonts)

def getprop(key, default=None, **kw):
	try:
		val = kw[key]
	except:
		val = default
	return val

# def detrend_3d(a):
# 	try:
# 		a = detrend(a,axis=0)
# 	except:
# 		for i in range(a.shape[1]):
# 			for j in range(a.shape[2]):
# 				try:
# 					a[:,i,j] = detrend(a[:,i,j])
# 				except:
# 					pass
# 	return a

def loadpickle(filename,verbose=False):
	a = pickle.load(open(filename,'rb'))
	if verbose:
		print('pickle loaded:',filename)
	return a

def savepickle(filename,a,verbose=True):
	if verbose:
		print('pickle save:',filename)
	f = open(filename,'wb')
	pickle.dump(a,f)
	f.close()

# y is an index
def fastcor(x, y):
	yv = y - y.mean()
	c = np.sqrt(np.sum(yv**2))
	if len(x.shape)>1:
		#print(x.shape)
		xv = x - x.mean(axis=0)
		a = np.sum(xv*yv[:,np.newaxis],axis=0)
		#print(a.shape)
		b = np.sqrt(np.sum(xv**2,axis=0))
		#print(b.shape)
		#print(c.shape)
	else:
		xv = x - x.mean()
		a = np.sum(xv*yv)
		b = np.sqrt(np.sum(xv**2))
	return a/(b*c)
	#xvss = np.sum(xv*xv,axis=0)
	#yvss = np.sum(yv*yv)
	#result = xv*yv[:,np.newaxis] / np.sqrt(xvss*yvss[:,np.newaxis])
	#result = np.matmul(xv.transpose(), yv) / np.sqrt(np.outer(xvss, yvss))
	#return np.maximum(np.minimum(result, 1.0), -1.0)

def psave(a,filename):
	f = open(filename,'wb')
	pickle.dump(a,f)
	f.close()
	
def hideaxes(ax):
	ax.spines['top'].set_visible(False)
	ax.spines['right'].set_visible(False)
	ax.spines['bottom'].set_visible(False)
	ax.spines['left'].set_visible(False)

def pimp_axes(ax=None,fontsize=FONTSIZE-2):
	if ax is None:
		ax = plt.gca()
	ax.tick_params(labelsize=fontsize,direction='inout')
	ax.yaxis.set_ticks_position('both')

def ecdf(sample):
    # convert sample to a numpy array, if it isn't already
    sample = np.atleast_1d(sample)
    # find the unique values and their corresponding counts
    quantiles, counts = np.unique(sample, return_counts=True)
    # take the cumulative sum of the counts and divide by the sample size to
    # get the cumulative probabilities between 0 and 1
    cumprob = np.cumsum(counts).astype(np.double) / sample.size
    return quantiles, cumprob

def daysinmonth(year,month):
	return calendar.monthrange(int(year),int(month))[1]

def spline(x,y,xnew):
	tck = interpolate.splrep(x, y, s=0)
	ynew = interpolate.splev(xnew, tck, der=0)
	return ynew

def set_tick_params(ax = None, labelsize = None):
	if ax is None:
		ax = plt.gca()
	if labelsize is None:
		labelsize = FONTSIZE-2
	ax.tick_params(labelsize=labelsize,tick2On=False,tickdir='out',width=.75)

#----------------------------------------------------------------------------
#from quikscat_daily_v4 import QuikScatDaily
#from matplotlib import cm

missing = -999.

def get_quikscat_date(dt): 
	if dt.hour < 1:
		dt -= timedelta(hours=24)
	if dt.hour>12 or dt.hour<1:
		timeofday = 'evening'
	else:
		timeofday = 'morning'
	return dt.date(), timeofday


def get_quikscat(
	dt = None, 
	timeofday = None
): 

	filename = '/Users/ewk/Sync/Data/QuikSCAT/qscat_%sv4.gz' %dt.strftime('%Y%m%d')

	dataset = QuikScatDaily(filename, missing=missing)
	if not dataset.variables: 
		sys.exit('file not found')

	iasc = (1 if timeofday == 'evening' else 0)
	wspdname = 'windspd'
	wdirname = 'winddir'

	# here is the data I will use:
	wspd = dataset.variables[wspdname][iasc,:,:]
	#wdir = dataset.variables[wdirname][iasc,:,:]
	land = dataset.variables['land'][iasc,:,:]
	gmt = dataset.variables['mingmt'][iasc,:,:]

	# get lon/lat:
	lon = dataset.variables['longitude']
	lat = dataset.variables['latitude']
	#print lon[:100]
	#raise
	# lon -= .5*(lon[1]-lon[0])
	# lat -= .5*(lat[1]-lat[0])
	lon,lat = np.meshgrid(lon,lat)

	#print lon.min(), lon.max(), lat.min(), lat.max()
	#raise
	lon[lon>180] -= 360
	I = np.nonzero((lat[:,0]>=45)&(lat[:,0]<=90))[0]
	J = np.nonzero((lon[0,:]>=-70)&(lon[0,:]<=60))[0]
	J = J[np.argsort(lon[0,J])]
	ix = np.ix_(I,J)

	return {
		'mingmt': gmt[ix],
		'lon': lon[ix],
		'lat': lat[ix],
		'wspd': wspd[ix],
		'land': land[ix]
	}

def tdhours(td):
	return (td.days * 24. + td.seconds / 3600.)


def find_closest(lon0, lat0, lon, lat):
	lat0r = np.radians(lat0)
	lon0r = np.radians(lon0)
	lat1r = np.radians(lat)
	lon1r = np.radians(lon)
	dlatr=lat1r-lat0r
	dlonr=lon1r-lon0r
	dist = np.sin(dlatr/2)**2 + np.cos(lat0r) * np.cos(lat1r) * np.sin(dlonr/2)**2
	return np.argsort(dist)[0]

def distance_between_two_points(lon0r, lat0r, lon1r, lat1r, km = True):
	dlatr=lat1r-lat0r
	dlonr=lon1r-lon0r
	a = np.sin(dlatr/2)**2 + np.cos(lat0r) * np.cos(lat1r) * np.sin(dlonr/2)**2
	return 2. * 6371. * np.arcsin(np.sqrt(a))


def computeadvection(lon,lat,a,u,v):
	if not len(a.shape) in [4,5]:
		print(a.shape)
		sys.exit('Invalid shape in computeadvection...')
	dlat = lat[1]-lat[0]
	#print(dlat)
	sy = np.sign(dlat)
	dlatr = np.radians(np.abs(dlat))
	#print(dlatr)
	dy = sy*2*(np.arctan2(np.sqrt((np.sin(dlatr/2))**2),np.sqrt(1-(np.sin(dlatr/2))**2)))*6371000
	#print(dy)
	#sys.exit()
	dy = np.ones((lat.shape[0],lon.shape[0]))*dy
	dx = np.empty((lat.shape))
	dlon = lon[1]-lon[0]
	sx = np.sign(dlon)
	dlonr = np.radians(np.abs(dlon))
	for i in range(lat.shape[0]):
		b = (np.cos(np.radians(lat[i]))**2)*(np.sin(dlonr/2)**2)
		dx[i] = sx * 2. * 6371000. * np.arcsin(np.sqrt(b))
		#c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a) )
		#dx[i] = c * 6371000
	dx = np.repeat(dx[:,np.newaxis],lon.shape,axis=1)
	#return dx, dy
	#dx,dy = calc_dx_dy(lon[0,:],lat[:,0])
	#print(dx[:3,:3])
	#print(dy[:3,:3])
	#sys.exit()
	#print(dx.shape,dy.shape,a.shape,u.shape,v.shape)
	#sys.exit()
	n = len(a.shape)
	if n == 5:
		dadx = np.gradient(a,axis=n-1)/dx[np.newaxis,np.newaxis,np.newaxis,:,:]
		dady = np.gradient(a,axis=n-2)/dy[np.newaxis,np.newaxis,np.newaxis,:,:]
	elif n == 4:
		dadx = np.gradient(a,axis=n-1)/dx[np.newaxis,np.newaxis,:,:]
		dady = np.gradient(a,axis=n-2)/dy[np.newaxis,np.newaxis,:,:]
	return -(u*dadx+v*dady)


def computedivergence(lon,lat,u,v):
	if not len(u.shape) in [4,5]:
		print(u.shape)
		sys.exit('Invalid shape in computeadvection...')
	dlat = lat[1]-lat[0]
	#print(dlat)
	sy = np.sign(dlat)
	dlatr = np.radians(np.abs(dlat))
	#print(dlatr)
	dy = sy*2*(np.arctan2(np.sqrt((np.sin(dlatr/2))**2),np.sqrt(1-(np.sin(dlatr/2))**2)))*6371000
	#print(dy)
	#sys.exit()
	dy = np.ones((lat.shape[0],lon.shape[0]))*dy
	dx = np.empty((lat.shape))
	dlon = lon[1]-lon[0]
	sx = np.sign(dlon)
	dlonr = np.radians(np.abs(dlon))
	for i in range(lat.shape[0]):
		b = (np.cos(np.radians(lat[i]))**2)*(np.sin(dlonr/2)**2)
		dx[i] = sx * 2. * 6371000. * np.arcsin(np.sqrt(b))
		#c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a) )
		#dx[i] = c * 6371000
	dx = np.repeat(dx[:,np.newaxis],lon.shape,axis=1)
	n = len(u.shape)
	if n == 5:
		dudx = np.gradient(u,axis=n-1)/dx[np.newaxis,np.newaxis,np.newaxis,:,:]
		dvdy = np.gradient(v,axis=n-2)/dy[np.newaxis,np.newaxis,np.newaxis,:,:]
	elif n == 4:
		dudx = np.gradient(u,axis=n-1)/dx[np.newaxis,np.newaxis,:,:]
		dvdy = np.gradient(v,axis=n-2)/dy[np.newaxis,np.newaxis,:,:]
	return dudx+dvdy
				
def reg_m(y, x):
	ones = np.ones(len(x[0]))
	import statsmodels.api as sm
	X = sm.add_constant(np.column_stack((x[0], ones)))
	for ele in x[1:]:
		X = sm.add_constant(np.column_stack((ele, X)))
	#results = sm.OLS(y, X).fit(cov_kwds={'alpha': 0.01})
	results = sm.OLS(y, X).fit()
	return results

def showgridlines(axis='both'):
	plt.grid(axis=axis, alpha=.5, lw=.5, ls='--')

def get_default_colors():
	prop_cycle = plt.rcParams['axes.prop_cycle']
	return prop_cycle.by_key()['color']
	
def savefig(filename,dpi=300,filetype='png'):
	filename += '.' + filetype
	plt.savefig(filename,dpi=dpi)

def get_colors_from_cmap(num_colors, name = "gist_stern_r"):
	from matplotlib.pylab import get_cmap
	cm = get_cmap(name)
	I = np.arange(num_colors) / (num_colors-1.)
	#print I
	#raise
	#return [cm((1.*i)/num_colors) for i in range(num_colors)]
	return [cm(i) for i in I]

def get_beaufort_colormap():
	colors = [
		[98,0,2],
		[199,0,10],
		[254,48,19],
		[231,168,32],
		[255,238,45],
		[255,219,91],
		[166,255,184]
	]
	return matplotlib.colors.ListedColormap(np.array(colors)/255., name='beaufort'), colors

def compute_gradient(a, lon, lat):
	#print lon[0,:]
	lon[lon>=180] -= 360.
	J = np.argsort(lon[0,:])
	lon = lon[:,J]
	#print a[0,10,:5]
	a = a[:,:,J]
	dlon = lon[0,1] - lon[0,0]
	dlat = lat[1,0] - lat[0,0]
	#print dlon, dlat
	#print lon[0,:]

	# dx in m:
	dx = 2. * np.cos(np.radians(lat)) * REARTH * np.pi / 360. * dlon
	#print dx[:,0]
	#print lat[:,0]
	# dy in m:
	dy = 2 * REARTH * np.pi / 360. * dlat
	#print dy
	#print dx, dy
	#raise

	# da / dx first:
	dadx = np.ones(a.shape) * np.nan
	dadx[:,:,1:-1] = 0.5 * (a[:,:,2:] - a[:,:,:-2])
	if (lon[0,-1] + dlon + lon[0,0]) < 0.5:
		dadx[:,:,0] = 0.5 * (a[:,:,1] - a[:,:,-1])
		dadx[:,:,-1] = 0.5 * (a[:,:,0] - a[:,:,-2])
	else:
		dadx[:,:,0] = a[:,:,1] - a[:,:,0]
		dadx[:,:,-1] = a[:,:,-1] - a[:,:,-2]
	dadx /= dx

	# da/dy:
	dady = np.ones(a.shape) * np.nan
	dady[:,1:-1,:] = (a[:,2:,:] - a[:,:-2,:]) / (2.*dy)
	dady[:,0,:] = (a[:,1,:] - a[:,0,:]) / dy
	dady[:,-1,:] = (a[:,-1,:] - a[:,-2,:]) / dy

	return (dadx, dady,)

	#print a[0,10,:5]
	#print a.shape
	#print lon[0,:]

def _interp(lon, lat, xr, yr):
	sz = np.prod(lon.shape)
	# Convert to radians and make 1D
	lonr = np.radians(lon).reshape((sz,))
	latr = np.radians(lat).reshape((sz,))
	dlatr=yr[np.newaxis,:]-latr[:,np.newaxis]
	dlonr=xr[np.newaxis,:]-lonr[:,np.newaxis]
	# Compute distance:
	b = np.sin(dlatr/2)**2 + np.cos(latr[:,np.newaxis]) * np.cos(yr[np.newaxis,:]) * np.sin(dlonr/2)**2
	b = 2. * 6371. * np.arcsin(np.sqrt(b))
	# Pick out 4 closest grid points for each point on the circle
	I = list(np.ogrid[[slice(x) for x in b.shape]])
	I[0] = b.argsort(0)[:4,:]
	c = b[I]
	# Create weights:
	w = np.empty(c.shape)
	# Just in case some grid points are really close, use weight 1:
	K = (c[0,:]<0.1*c[1,:])
	if np.sum(K)>0:
		w[:,K] = np.array([1., 0., 0., 0.])[:,np.newaxis]
	# Now the normal points:
	K = (~K)
	# Weight by inverse of distance:
	w[:,K] = c[:,K]**(-1)
	# Normalize to 1:
	w[:,K] /= np.sum(w[:,K], axis=0)
	return w, I, sz

def interpolate_to_grid2(a, lon, lat, xr, yr, param = None):
	print("Finding weights...")
	w, I, sz = _interp(lon, lat, xr, yr)
	a = a.reshape((a.shape[0], sz,))
	oo = np.ones(xr.shape)
	ret = np.empty((a.shape[0], xr.shape[0],))
	prev = 0
	print("Applying weights...")
	for j in range(a.shape[0]):
		perc = int(100.*(j+1.)/a.shape[0]+.5)
		if perc >= prev + 10:
			prev = perc-perc%10
			print("%i%%..."%prev)
		c = a[j,:][:,np.newaxis] * oo
		ret[j,:] = np.sum(c[I]*w, axis=0)
	return ret

def interpolate_simple(a, lon0, lat0, lon1, lat1):
	sz = np.prod(lon1.shape)
	xr = np.radians(lon1.reshape((sz,)))
	yr = np.radians(lat1.reshape((sz,)))
	b = interpolate_to_grid([a], lon0, lat0, xr, yr)
	return b[0]

def interpolate_between_grids(a, lon0, lat0, lon1, lat1):
	sz = np.prod(lon1.shape)
	xr = np.radians(lon1.reshape((sz,)))
	yr = np.radians(lat1.reshape((sz,)))
	b = interpolate_to_grid2(a, lon0, lat0, xr, yr)
	b = b.reshape(a.shape)
	return b

def interpolate_to_grid(aa, lon, lat, xr, yr, param = None):
	w, I, sz = _interp(lon, lat, xr, yr)
	ret = []
	for a in aa:
		a = a.reshape((sz,))
		c = a[:,np.newaxis] * np.ones(xr.shape)
		ret.append(np.sum(c[I]*w, axis=0))
	return ret

def running_mean(x, N):
	window = np.ones(int(N))/float(N)
	return np.convolve(x, window, 'valid')
	#return np.convolve(x, window, 'same')

def trim(a,cv):
	zi = np.array(a)
	zi[zi<cv[0]] = cv[0]
	zi[zi>cv[-1]] = cv[-1]
	return zi
	