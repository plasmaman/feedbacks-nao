from ewkutils import *
from subplotfigure import *
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import xarray as xr
import pandas as pd
from glob import glob
from datetime import date, datetime, timedelta
np.seterr(invalid='ignore')
import cartopy.crs as ccrs
import cartopy
import cartopy.feature as cf
from netCDF4 import num2date, Dataset
from eofs.standard import Eof
#from eofs.xarray import Eof
from scipy.stats import pearsonr
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
from matplotlib.ticker import MultipleLocator
import matplotlib.patches as mpatches
import string
from calendar import monthrange
import cmcrameri.cm as cmc
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import norm
from scipy.ndimage import gaussian_filter
mpl.rcParams['hatch.linewidth'] = 0.5


expname = 'feedbacks2'
datadir = '%s/%s'%(DATADIR,expname)
cachedir = '%s/cache/python/%s'%(DATADIR,expname)
figdir = '%s/Figs/%s'%(HOMEDIR,expname)

NAO_MONTHS = [12, 1, 2]
SST_MONTHS = [11]
ENSEMBLE_MEAN = False
INITMONTHS = [11]
mstr = ','.join(['%i'%i for i in INITMONTHS])
DAYSINMONTH = [31,28.25,31,30,31,30,31,31,30,31,30,31]
VALPERIOD = [1981,2023]
ALL = 'ALL'
NAOREGION = 'NAOREGION'
SSTREGION = 'SSTREGION_CF'
SPG = 'SPG'
EGR = 'EGR'
DREGION = 'DREGION'
COASTLINEWIDTH = 0.6
COASTLINECOLOR = 'k'
LANDCOLOR = '#e4ca8b'
BORDERCOLOR = 'brown'
TWI = 6.85 # 17.4 cm
fs = FONTSIZE
FLUX_VAR = 'slhf+sshf'

CBOXES = {
	'ALL': [-20,80,-100,60],
	'DREGION': [20,70,-90,20],
	'SPG': [50,60,-56,-25], # second sub
	'EGR': [45,55,-53,-25], # second sub
	'STUDY': [45,60,-50,-25],
	'NAOREGION': [20,80,-90,40],
	'SSTREGION_CF': [20,70,-100,20],
	'TROPICAL_NA': [0,20,-100,20],
	'SSTREGION': [0,75,-100,20],
	'SSTREGION_R1': [0,70,-100,20],
	'EUR2': [34,72,-12,42],
	'GLOBAL': [-90,90,-180,180]
}

def draw_letter(ax, xpos, ypos, letter_number, zorder=None):
	ax.text(xpos, ypos,
		string.ascii_lowercase[letter_number],
		transform=ax.transAxes,
		fontsize=fs+1, fontweight='bold',
		va='top', ha='left', zorder=zorder,
		bbox=dict(facecolor='white', edgecolor='k', boxstyle='square'))

def append_to_e(e, **kw):
	try:
		ignore_initmonths = kw['ignore_initmonths']
	except:
		ignore_initmonths = False
	if not ignore_initmonths:
		e.append('init_'+','.join(['%02d'%i for i in INITMONTHS]))
	e.append('-'.join(['%i'%(i) for i in VALPERIOD]))
	try:
		ignore_regions = kw['ignore_regions']
	except:
		ignore_regions = False
	if not ignore_regions:
		e.append('nao_area_'+'_'.join('%.1f'% i for i in CBOXES[NAOREGION]))
		e.append(','.join(['%02d'%i for i in NAO_MONTHS]))
		e.append('sst_area_'+'_'.join('%.1f'% i for i in CBOXES[SSTREGION]))
		e.append(','.join(['%02d'%i for i in SST_MONTHS]))

def pimp_axes(ax=None,fontsize=FONTSIZE-2):
	if ax is None:
		ax = plt.gca()
	ax.tick_params(labelsize=fontsize,direction='inout')
	#ax.yaxis.set_ticks_position('both')

def draw_map_border(ax, zorder=1000):
	rect = mpatches.Rectangle(
		(ax.get_xlim()[0], ax.get_ylim()[0]),       # lower-left corner
		np.diff(ax.get_xlim())[0],                  # width
		np.diff(ax.get_ylim())[0],                  # height
		linewidth=1.5, edgecolor='k', facecolor='none', zorder=zorder)
	ax.add_patch(rect)

def plot_box(ax, name, color='k', linewidth=.75, zorder=200, **kwargs):
    """
    Draws a rectangular box outline for a named region in CBOXES.
    Parameters
    ----------
    ax : matplotlib axis
        Axis to plot on.
    name : str
        Name of the box, must be a key in CBOXES.
    kwargs : dict
        Extra arguments passed to ax.plot (e.g. color, linestyle).
    """
    if name not in CBOXES:
        raise ValueError(f"Region {name} not in CBOXES")
    latmin, latmax, lonmin, lonmax = CBOXES[name]
    lats = [latmin, latmin, latmax, latmax, latmin]
    lons = [lonmin, lonmax, lonmax, lonmin, lonmin]
    ax.plot(lons, lats, linestyle="--", color=color, linewidth=linewidth, zorder=zorder, **kwargs)

class SubplotFigure(SubplotFigureBase):
	def __init__(self,**kw):
		super().__init__(**kw)
		self.letter_format = '%s'
		#self.letter_format = '(%s)'
		self.letter_fontsize = FONTSIZE
		#self.letter_fontweight = 'normal'
		self.letter_fontweight = 'bold'
		#self.letter_offsetx_inches = 0.02
		self.letter_offsetx_inches=0.07
		self.letter_offsety_inches=0.05
		#self.letter_offsety_inches = 0.1

def getmapfig(**kw):
	defaults = {
		'figw_inches': TWI,
		'cbar_width_percent': 99,
		'kind': 'map',
		'margintop_inches': 0.24,
		#'margintop_inches': 0.4,
		'marginbottom_inches': 0.07
	}
	try:
		vbar = kw['vbar']
	except:
		vbar = False
	if vbar:
		defaults['cbar_width_inches'] = .1
		defaults['cbar_rightpadding_inches'] = .45
		defaults['cbar_leftpadding_inches']= 0.05
	else:
		defaults['cbar_height_inches'] = .1
		defaults['cbar_bottompadding_inches'] = .22
		defaults['cbar_toppadding_inches'] = 0.08
	for k,v in defaults.items():
		if not k in kw:
			kw[k] = v
	return SubplotFigure(
		**kw
	)

def check_year(dt):
	#if not dt.month in SEASON:
	#	return False
	y0 = VALPERIOD[0] + int((1 if dt.month<7 else 0))
	y1 = y0 + np.diff(VALPERIOD)[0]
	#print(dt.month,dt.year,y0,y1)
	if dt.year < y0 or dt.year > y1:
		#print('False')
		return False
	#print('True')
	return True

def getg():
	ds = Dataset('%s/era5_11_1981-2023_sfc.nc'%(datadir), mode='r')
	lon = ds.variables['longitude'][:]
	#lon[lon>180] -= 360
	#lon = lon[np.argsort(lon)]
	lat = ds.variables['latitude'][:]
	lon,lat = np.meshgrid(lon,lat)
	return {
		'lon': lon,
		'lat': lat
	}

def savefig(filename,dpi=600,filetype='png'):
	filename += '.' + filetype
	plt.savefig(filename,dpi=dpi)

def subc(region = None):
	g = getg()
	if region is None:
		bbox = (
			np.min(g['lat'].ravel()),
			np.max(g['lat'].ravel()),
			np.min(g['lon'].ravel()),
			np.max(g['lon'].ravel()),
		)
	else:
		bbox = CBOXES[region]
	J4 = np.nonzero((g['lon'][0,:]>=bbox[2])&(g['lon'][0,:]<=bbox[3]))[0]
	I4 = np.nonzero((g['lat'][:,0]>=bbox[0])&(g['lat'][:,0]<=bbox[1]))[0]
	K4 = np.nonzero(
		(g['lon'].ravel()>=bbox[2])&
		(g['lon'].ravel()<=bbox[3])&
		(g['lat'].ravel()>=bbox[0])&
		(g['lat'].ravel()<=bbox[1])
	)[0]
	ix4 = np.ix_(I4,J4)
	lon4 = g['lon'][ix4]
	lat4 = g['lat'][ix4]
	try:
		lsm4 = g['lsm'][ix4]
	except:
		lsm4 = None
	asp4 = (np.max(lon4.ravel())-np.min(lon4.ravel())) / (np.max(lat4.ravel())-np.min(lat4.ravel()))
	d = {
		'lon': lon4,
		'lat': lat4,
		'lsm': lsm4,
		'I': I4,
		'J': J4,
		'K': K4,
		'ix': ix4,
		'sz': np.prod(lon4.shape),
		'asp': asp4
	}
	d['proj'] = ccrs.PlateCarree()
	d['extent'] = [bbox[2],bbox[3],bbox[0],bbox[1]]
	return d

def drawborders(ax):
	b = cartopy.feature.NaturalEarthFeature(category='cultural',name='admin_0_boundary_lines_land',scale=resol,facecolor='none')
	#b = cf.BORDERS
	ax.add_feature(b,edgecolor=BORDERCOLOR,linewidth=COASTLINEWIDTH*.75)
	#ax.add_feature(b,edgecolor='yellow',linewidth=COASTLINEWIDTH)

def drawfeatures(ax, fill_land = True, zorder = 100):
	if fill_land:
		ax.add_feature(cf.LAND, facecolor=LANDCOLOR, edgecolor=COASTLINECOLOR, linewidth=COASTLINEWIDTH, zorder=zorder)
	else:
		ax.add_feature(cf.COASTLINE,edgecolor='w',linewidth=COASTLINEWIDTH*1.6)
		ax.add_feature(cf.COASTLINE,edgecolor=COASTLINECOLOR,linewidth=COASTLINEWIDTH)
	ax.add_feature(cf.LAKES,edgecolor=COASTLINECOLOR,linewidth=COASTLINEWIDTH*.75,facecolor='None')

class Model(object):

	def __init__(self,**kw):
		self.modelname = kw['modelname']
		self.climperiod =  {
			'ecmwf': [1981,2016],
			'ukmo': [1993,2016],
			'meteo_france': [1993,2018],
			'dwd': [1993,2019],
			'jma': [1993,2016],
			'cmcc': [1993,2016],
			'eccc': [1993,2020],
			'ncep': [1993,2016]
		}[self.modelname]
		#self.fileprefix = '%s/%s_*_%i-%i'%(
		self.fileprefix = '%s/%s_*'%(
			datadir,
			self.modelname
			#self.climperiod[0],
			#self.climperiod[1]
		)

	def get_var_alias(self, **kw):
		try:
			return {
				'slhf': 'mslhfl',
				'sshf': 'msshfl',
				'tp': 'tprate'
			}[kw['variable']]
		except:
			return kw['variable']

	def get_suffix(self, **kw):
		if kw['variable'] in ['msl','sst']:
			return 'sfc'
		if kw['variable'] in ['slhf','sshf','tp']:
			return 'flx'
		return 'plev'

	def get_data(self,**kw):
		e = [
			'modeldata',
			self.modelname,
			','.join(['%02d'%i for i in kw['months']]),
			kw['variable']
		]
		try:
			level = kw['level']
			e.append('@%i'%(level))
		except:
			level = None
		append_to_e(e, ignore_regions=True, ignore_initmonths=(self.modelname in ['era5']))
		cachefile = '%s/mdata/%s'%(cachedir,'_'.join(e))
		try:
			data = loadpickle(cachefile)
		except:
			data = None
			for v in kw['variable'].split('+'):

				if v in ['egr','bvf','dvdz']:
					kw2 = kw.copy()
					levs = [850,700]
					a = {}
					for vv in ['u','v','t','z']:
						for lev in levs:
							kw2['variable'] = vv
							kw2['level'] = lev
							v2 = '%s@%i'%(vv,lev)
							#print(v2)
							b = self.read_data(**kw2)
							if vv=='z':
								b /= 9.81
							if vv=='t':
								b *= (1000/lev)**0.286
							a[v2] = b
							#print(vv,lev,b.shape)
							# 1. Check for NaNs per year
					d = {}
					for vv in ['u','v','t','z']:
						d[vv] = a['%s@%i'%(vv,levs[1])] - a['%s@%i'%(vv,levs[0])]
					theta = 0.5*(a['t@%i'%levs[0]]+a['t@%i'%levs[1]])
					N = np.sqrt((9.81/theta)*(d['t']/d['z']))
					if v=='bvf':
						a = N
					else:
						dudz = d['u']/d['z']
						dvdz = d['v']/d['z']
						if variable=='dvdz':
							a = np.sqrt(dudz**2+dvdz**2)
						else:
							if len(N.shape)==5:
								f = np.abs(np.sin(np.radians(g['lat']))[np.newaxis,np.newaxis,np.newaxis,:,:])
							elif len(N.shape)==4:
								f = np.abs(np.sin(np.radians(g['lat']))[np.newaxis,np.newaxis,:,:])
							else:
								f = np.abs(np.sin(np.radians(g['lat']))[np.newaxis,:,:])
							omega = 7.2921159e-5
							f *= 2*omega
							a = 0.3098 * f * np.sqrt(dudz**2+dvdz**2) / N * 86400

				elif v == 'dtdy':
					kw2 = kw.copy()
					levs = [850,700]
					kw2['variable'] = 't'
					t = []
					for lev in levs:
						kw2['level'] = lev
						t.append(self.read_data(**kw2))
					t = np.mean(t,axis=0)
					print(t.shape)
					t_ = t.reshape(list(t.shape[:-2]) + list(t.shape[-2:]))
					dy = g['lat'][1,0] - g['lat'][0,0]
					dt = np.empty(t_.shape)
					dt[:,:-1,:] = t_[:,1:,:] - t_[:,:-1,:]
					dt[:,-1,:] = t_[:,-1,:] - t_[:,-2,:]
					#a = (dt/dy).reshape(t.shape)
					a = np.abs(dt/dy).reshape(t.shape)
				else:
					kw2 = kw.copy()
					kw2['variable'] = v
					a = self.read_data(**kw2)
					if v in ['slhf','sshf']:
						a *= -1
				data = (a if data is None else a+data)
			savepickle(cachefile, data)
		return data

	def read_data(self, **kw):
		sub = subc()
		e = [
			'modeldata',
			self.modelname,
			'_'.join('%.1f'% i for i in CBOXES[ALL]),
			','.join(['%02d'%i for i in kw['months']]),
			kw['variable']
		]
		try:
			level = kw['level']
			e.append('@%i'%(level))
		except:
			level = None
		append_to_e(e)
		variable = kw['variable']
		alias = self.get_var_alias(**kw)
		cachefile = '%s/%s'%(cachedir,'_'.join(e))
		try:
			data = loadpickle(cachefile)
		except:

			data = None
			init_years_all = []   # year of forecast_reference_time per kept time slot
			init_months_all = []  # month of forecast_reference_time (for stable ordering)

			for initmonth in INITMONTHS:
				filenames = sorted(glob('%s_%02d*_%s.nc' % (self.fileprefix, initmonth, self.get_suffix(variable=variable))))

				for filename in filenames:
					print(filename)
					if VALPERIOD[-1] < 2017 and '2017' in filename:
						print('Skipping forecast file...')
						continue

					ds = Dataset(filename, mode='r')

					def gettime(tname):
						times = ds.variables[tname][:]
						time_units = ds.variables[tname].getncattr('units')
						time_cal = ds.variables[tname].getncattr('calendar')
						return num2date(times, units=time_units, calendar=time_cal)

					if 'time' in ds.variables:
						sys.exit('Whoops, expected forecastMonth...')
					elif 'forecastMonth' in ds.variables:
						t = gettime('forecast_reference_time')  # init times
						if t is None:
							sys.exit("Invalid time variable...")

						fmonths = ds.variables['forecastMonth'][:]

						b_list = []
						init_years_this = None
						init_months_this = None

						for j, fmonth in enumerate(fmonths):
							# build *valid* times (only for filtering by target calendar month/year)
							valid_times = [dt0 + timedelta(days=int(31 * (fmonth - 1))) for dt0 in t]

							idx = []
							for i, vdt in enumerate(valid_times):
								if vdt.month in kw['months'] and check_year(vdt):
									idx.append(i)
							if len(idx) == 0:
								continue

							# slice data: (member, time, lat, lon)
							a = ds.variables[alias][:, idx, j, :, :]
							if a.shape[0] > 25:
								a = a[:25, ...]
							if level is not None:
								levs = ds['pressure_level'][:]
								lev = np.nonzero(np.array(levs).astype(int) == level)[0]
								a = a[:, :, lev, :, :].squeeze(axis=2)

							b_list.append(a)

							# crucial: tag by INIT (forecast_reference_time) year/month for each kept time index
							yidx = [t[i].year for i in idx]
							midx = [t[i].month for i in idx]

							if init_years_this is None:
								init_years_this = yidx
								init_months_this = midx
							else:
								if (len(init_years_this) != len(yidx) or
									any(y0 != y1 for y0, y1 in zip(init_years_this, yidx)) or
									any(m0 != m1 for m0, m1 in zip(init_months_this, midx))):
									raise RuntimeError("Inconsistent init-year/month indexing across forecastMonth in file: %s" % filename)

						if len(b_list) == 0:
							ds.close()
							continue

						b = np.stack(b_list, axis=0)  # (fmonth_kept, member, time, lat, lon)

						if data is None:
							data = b
							init_years_all.extend(init_years_this)
							init_months_all.extend(init_months_this)
						else:
							if data.shape[0] != b.shape[0] or data.shape[1] != b.shape[1] or data.shape[3:] != b.shape[3:]:
								raise RuntimeError("Shape mismatch before concat: %s vs %s" % (data.shape, b.shape))
							data = np.concatenate((data, b), axis=2)  # concat along time
							init_years_all.extend(init_years_this)
							init_months_all.extend(init_months_this)

						ds.close()
					else:
						sys.exit("Don't know how to read data...")

			# ---- order by forecast_reference_time (init year, then month) ----
			if data is None:
				return None
			if len(init_years_all) != data.shape[2] or len(init_months_all) != data.shape[2]:
				raise RuntimeError("Init year/month list length does not match time axis")

			order = np.lexsort((np.asarray(init_months_all), np.asarray(init_years_all)))  # sort by year, then month
			data = data[:, :, order, :, :]  # reorder time axis

			# now (fmonth, member, time, lat, lon) -> final (month, year, member, lat, lon)
			data = np.swapaxes(data, 1, 2)

		return data


	
	def get_seasonal_data(self, **kw):
		try:
			data = kw['data']
		except:
			data = self.get_data(**kw)
		if len(kw['months']) > 1:
			fac = [1.*DAYSINMONTH[m-1] for m in kw['months']]
			data = np.sum([j*data[i] for i,j in enumerate(fac)],axis=0) / np.sum(fac)
			#print(data.shape)
		else:
			data = data.squeeze(axis=0)
		if kw['variable'] == 'msl':
			data /= 100
		return data

	def get_sst_index(self, **kw):
		#return self.get_sst_index_dynamic(**kw)
		#refmonth = kw['refmonth']
		e = [
			'sst_idx_fixed',
			self.modelname
		]
		append_to_e(e)
		cachefile = '%s/%s'%(cachedir,'_'.join(e))
		try:
			sst_idx = loadpickle(cachefile)
		except:
			era5 = ERA5()
			dic = era5.get_beta(**kw)
			sub_sst = dic['sub']
			w = dic['weights']
			beta = dic['beta']
			den = np.sum(w * beta * beta)
			sst_tm1 = self.get_seasonal_data(variable = 'sst', months=[11])
			sst_tm1 = sst_tm1.reshape([np.prod(sst_tm1.shape[:2])] + list(sst_tm1.shape[2:]))
			sst_tm1 = sst_tm1[np.ix_(range(sst_tm1.shape[0]),sub_sst['I'],sub_sst['J'])]
			sst_tm1 = sst_tm1.reshape([sst_tm1.shape[0], np.prod(sst_tm1.shape[1:])])
			#sst_tm1 = (sst_tm1 - np.mean(sst_tm1, axis=0)[np.newaxis,:]) / np.std(sst_tm1, axis=0)[np.newaxis,:]
			sst_tm1 -= np.mean(sst_tm1, axis=0, keepdims=True)
			# Weighted projection
			# print(sst_tm1.shape)
			# print(np.sum(np.isnan(np.mean(sst_tm1, axis=0).ravel())))
			# print(np.sum(~np.isnan(np.mean(sst_tm1, axis=0).ravel())))
			# sys.exit()
			#sst_idx = np.sum(np.sum(a * beta[np.newaxis,:,:] * w[np.newaxis,:,:], axis=1), axis=1)
			sst_idx = np.nansum(sst_tm1 * beta.ravel()[np.newaxis,:] * w.ravel()[np.newaxis,:], axis=1)
			sst_idx = (sst_idx - np.mean(sst_idx)) / np.std(sst_idx, ddof=1)
			# num_ts = np.tensordot(sst_tm1, w * beta, axes=([1,2],[0,1]))	# (nsamp,)
			# sst_nao_idx = num_ts / den
			# sst_nao_idx = (sst_nao_idx - sst_nao_idx.mean()) / sst_nao_idx.std()
		return sst_idx

	def get_sst_index_dynamic(self, **kw):
		lag = kw['lag']
		refmonth = kw['refmonth']
		e = [
			'sst_idx',
			self.modelname,
			'lag_%i'%(lag),
			'refmonth_%i'%(refmonth)
		]
		append_to_e(e)
		cachefile = '%s/%s'%(cachedir,'_'.join(e))
		try:
			sst_idx = loadpickle(cachefile)
		except:
			era5 = ERA5()
			dic = era5.get_beta(**kw)
			sub_sst = dic['sub']
			w = dic['weights']
			beta = dic['beta']
			den = np.sum(w * beta * beta)
			tm1 = refmonth - lag
			if tm1 <= 0:
				tm1 += 12
			sst_tm1 = self.get_seasonal_data(variable = 'sst', months=[tm1])
			sst_tm1 = sst_tm1.reshape([np.prod(sst_tm1.shape[:2])] + list(sst_tm1.shape[2:]))
			sst_tm1 = sst_tm1[np.ix_(range(sst_tm1.shape[0]),sub_sst['I'],sub_sst['J'])]
			sst_tm1 = sst_tm1.reshape([sst_tm1.shape[0], np.prod(sst_tm1.shape[1:])])
			#sst_tm1 = (sst_tm1 - np.mean(sst_tm1, axis=0)[np.newaxis,:]) / np.std(sst_tm1, axis=0)[np.newaxis,:]
			sst_tm1 -= np.mean(sst_tm1, axis=0, keepdims=True)
			# Weighted projection
			# print(sst_tm1.shape)
			# print(np.sum(np.isnan(np.mean(sst_tm1, axis=0).ravel())))
			# print(np.sum(~np.isnan(np.mean(sst_tm1, axis=0).ravel())))
			# sys.exit()
			#sst_idx = np.sum(np.sum(a * beta[np.newaxis,:,:] * w[np.newaxis,:,:], axis=1), axis=1)
			sst_idx = np.nansum(sst_tm1 * beta.ravel()[np.newaxis,:] * w.ravel()[np.newaxis,:], axis=1)
			sst_idx = (sst_idx - np.mean(sst_idx)) / np.std(sst_idx, ddof=1)
			# num_ts = np.tensordot(sst_tm1, w * beta, axes=([1,2],[0,1]))	# (nsamp,)
			# sst_nao_idx = num_ts / den
			# sst_nao_idx = (sst_nao_idx - sst_nao_idx.mean()) / sst_nao_idx.std()
		return sst_idx

	
	def get_nao(self, **kw):
		e = [
			'nao_proj',
			self.modelname,
			'months_'+','.join(['%02d'%i for i in kw['months']])
		]
		append_to_e(e)
		cachefile = '%s/%s'%(cachedir,'_'.join(e))
		try:
			proj = loadpickle(cachefile)
		except:
			data = self.get_seasonal_data(variable = 'msl', **kw)
			# Collapse first two dimensions:
			data2 = data.reshape([np.prod(data.shape[:2])] + list(data.shape[2:]))
			sub3 = subc(region = NAOREGION)
			data3 = data2[np.ix_(range(data2.shape[0]),sub3['I'],sub3['J'])]
			data3 -= np.mean(data3, axis=0, keepdims=True)
			solver = ERA5().get_ref_nao()
			proj = solver.projectField(data3, neofs=1)  # shape (nyears*nmember,)
			proj = (proj - proj.mean()) / proj.std(ddof=1)
		if VALPERIOD[0]==2001 and VALPERIOD[-1]==2023:
			proj *= -1
		return proj
		

class ERA5(Model):

	def __init__(self,**kw):
		self.modelname = 'era5'
		self.climperiod =  [1981,2016]

	def get_ref_nao(self, **kw):
		e = [
			'ref_nao_djf',
			','.join(['%02d'%i for i in NAO_MONTHS]),
			self.modelname
		]
		append_to_e(e)
		cachefile = '%s/%s'%(cachedir,'_'.join(e))
		try:
			solver = loadpickle(cachefile)
		except:
			data = self.get_seasonal_data(variable = 'msl', months=NAO_MONTHS)
			# Collapse first two dimensions:
			data2 = data.reshape([np.prod(data.shape[:2])] + list(data.shape[2:]))
			#print(data2.shape)
			sub3 = subc(region = NAOREGION)
			data3 = data2[np.ix_(range(data2.shape[0]),sub3['I'],sub3['J'])]
			data3 -= np.mean(data3, axis=0, keepdims=True)
			#print(data3.shape)
			w = np.sqrt(np.cos(np.deg2rad(sub3['lat'])))
			solver = Eof(data3,weights=w)
			savepickle(cachefile, solver)
		return solver


	def get_beta(self, **kw):
		#refmonth = kw['refmonth']
		e = [
			'beta_fixed',
			','.join(['%02d'%i for i in SST_MONTHS]),
			','.join(['%02d'%i for i in NAO_MONTHS]),
			self.modelname
		]
		append_to_e(e)
		cachefile = '%s/%s'%(cachedir,'_'.join(e))
		try:
			dic = loadpickle(cachefile)
		except:

			data = self.get_seasonal_data(variable = 'sst', months=SST_MONTHS)
			data2 = data.reshape([np.prod(data.shape[:2])] + list(data.shape[2:]))
			sub3 = subc(region = SSTREGION)
			data3 = data2[np.ix_(range(data2.shape[0]),sub3['I'],sub3['J'])]
			sst_tm1 = data3 - np.mean(data3, axis=0, keepdims=True)
			# Weights
			w = np.cos(np.deg2rad(sub3['lat']))
			nao_t = self.get_nao(months = NAO_MONTHS).ravel()
			beta = np.tensordot(nao_t, sst_tm1, axes=(0, 0)) / len(nao_t)	# (nlat, nlon)

			dic = {
				'beta': beta,
				'weights': w,
				'sub': sub3
			}
			savepickle(cachefile, dic)
		return dic

	def get_beta_(self, **kw):
		#refmonth = kw['refmonth']
		e = [
			'beta_new',
			self.modelname,
			'lag_%i'%(kw['lag']),
			#'refmonth_%i'%(refmonth)
		]
		append_to_e(e)
		cachefile = '%s/%s'%(cachedir,'_'.join(e))
		try:
			dic = loadpickle(cachefile)
		except:

			data = self.get_seasonal_data(variable = 'sst', months=[11, 12, 1])
			data2 = data.reshape([np.prod(data.shape[:2])] + list(data.shape[2:]))
			sub3 = subc(region = SSTREGION)
			data3 = data2[np.ix_(range(data2.shape[0]),sub3['I'],sub3['J'])]
			sst_tm1 = data3 - np.mean(data3, axis=0, keepdims=True)
			# Weights
			w = np.cos(np.deg2rad(sub3['lat']))
			nao_t = self.get_nao(months = [12, 1, 2]).ravel()
			beta = np.tensordot(nao_t, sst_tm1, axes=(0, 0)) / len(nao_t)	# (nlat, nlon)

			dic = {
				'beta': beta,
				'weights': w,
				'sub': sub3
			}
			savepickle(cachefile, dic)
			# print(sst_tm1.shape)
			# cc = fastcor(sst_tm1.reshape([sst_tm1.shape[0],np.prod(sub_sst['lat'].shape)]),nao_t)
			# print(nao_t.shape,cc.shape)
			# cc = cc.reshape(sub_sst['lat'].shape)
			# plt.figure()
			# plt.contourf(beta)
			# plt.figure()
			# plt.contourf(cc)
		return dic

	def get_beta_dynamic(self, **kw):
		#refmonth = kw['refmonth']
		e = [
			'beta_new',
			self.modelname,
			'lag_%i'%(kw['lag']),
			#'refmonth_%i'%(refmonth)
		]
		append_to_e(e)
		cachefile = '%s/%s'%(cachedir,'_'.join(e))
		try:
			dic = loadpickle(cachefile)
		except:

			data = self.get_seasonal_data(variable = 'msl', months=[11, 12, 1])
			data2 = data.reshape([np.prod(data.shape[:2])] + list(data.shape[2:]))
			sub3 = subc(region = SSTREGION)
			data3 = data2[np.ix_(range(data2.shape[0]),sub3['I'],sub3['J'])]
			sst_tm1 = data3 - np.mean(data3, axis=0, keepdims=True)
			# Weights
			w = np.cos(np.deg2rad(sub3['lat']))
			nao_t = self.get_nao(months = [12, 1, 2]).ravel()
			beta = np.tensordot(nao_t, sst_tm1, axes=(0, 0)) / len(nao_t)	# (nlat, nlon)

			dic = {
				'beta': beta,
				'weights': w,
				'sub': sub3
			}
			savepickle(cachefile, dic)
		return dic

	
	def get_var_alias(self, **kw):
		try:
			return {
				'slhf': 'avg_slhtf',
				'sshf': 'avg_ishf'
			}[kw['variable']]
		except:
			return kw['variable']

	def read_data(self,**kw):
		months = kw['months']
		variable = kw['variable']
		alias = self.get_var_alias(**kw)
		sub = subc()
		e = [
			'modeldata',
			self.modelname,
			'_'.join('%.1f'% i for i in CBOXES[ALL]),
			','.join(['%02d'%i for i in months]),
			variable
		]
		try:
			level = kw['level']
			e.append('@%i'%level)
		except:
			level = None
		append_to_e(e)
		cachefile = '%s/%s'%(cachedir,'_'.join(e))
		try:
			data = loadpickle(cachefile)
		except:
			#print('Collecting ERA5 data...')
			data = []
			for month in months:
				wildcard = '%s/era5_%02d*_%s.nc'%(datadir,month,self.get_suffix(variable=variable))
				# print('*'*10)
				#print(wildcard)
				filename =  glob(wildcard)[0]
				# print(filename) 
				ds = xr.open_dataset(filename, engine="h5netcdf")
				# Check which time-like coordinate exists
				# print(f"{filename} dims: {ds.dims}")
				# print(f"{filename} coords: {list(ds.coords)}")

				if 'time' in ds.dims:
					time_name = 'time'
					dates = pd.to_datetime(ds[time_name].values)

				elif 'valid_time' in ds.dims:
					time_name = 'valid_time'
					dates = pd.to_datetime(ds[time_name].values, unit='s')

				elif 'date' in ds.dims:
					time_name = 'date'
					dates = pd.to_datetime(ds[time_name].values, format="%Y%m%d")

				else:
					print(f"Warning: no recognised time dimension in {filename}")
					time_name = None
					dates = None

				# Apply mask only if we have a time dimension
				if time_name is not None:
					mask = [check_year(dt) for dt in dates]
					ds = ds.isel({time_name: mask})

				# Variable selection
				a = ds[alias]

				# Pressure-level selection if requested
				if level is not None:
				    levs = ds['pressure_level'].values.astype(int)
				    lev_idx = np.where(levs == level)[0]
				    if len(lev_idx) == 0:
				        raise ValueError(f"Requested level {level} not found in dataset")
				    a = a.sel(pressure_level=levs[lev_idx[0]])

				# Convert to numpy if needed
				a = a.values

				data.append(a)
			data = np.array(data)[:,:,np.newaxis]
		return data

def create_model(modelname):
	if modelname == 'era5':
		return ERA5()
	else:
		return Model(modelname = 'ecmwf')


def regress_all(nao, sst, flux):
	"""
	Compute tau (scalar), tau_prime (ngrid,), alpha (ngrid,), beta (ngrid,)
	nao:   (nsamp,)
	sst:   (nsamp,)
	flux:  (nsamp, ngrid)
	"""
	valid = np.isfinite(nao) & np.isfinite(sst) & np.isfinite(flux).all(axis=1)
	nao, sst, flux = nao[valid], sst[valid], flux[valid]

	# tau (scalar)
	tau = np.dot(sst, nao) / np.dot(sst, sst)

	# alpha(j): slope of flux_j ~ sst
	alpha = np.dot(sst, flux) / np.dot(sst, sst)   # shape (ngrid,)

	ss = np.dot(sst, sst)
	sf = np.dot(sst, flux)        # (ngrid,)
	ff = np.sum(flux*flux, axis=0)  # (ngrid,)
	sy = np.dot(sst, nao)
	fy = np.dot(flux.T, nao)      # (ngrid,)

	# determinant for each j
	den = ss*ff - sf*sf

	tau_prime = (ff*sy - sf*fy)/den
	beta = (ss*fy - sf*sy)/den

	return tau, tau_prime, alpha, beta


def standardize(data, axis=0):
	return (data - np.mean(data, axis=axis, keepdims=True)) / np.std(data, axis=axis, ddof=1, keepdims=True)

def plot_cbar_below(fig, ax, im, extend='both'):
	fig_w, fig_h = fig.fig.get_size_inches()
	dims = fig.get_cbar_dims()
	# axes position in figure coordinates
	bbox = ax.get_position()
	x0_fig, y0_fig, w_fig, h_fig = bbox.x0, bbox.y0, bbox.width, bbox.height
	# convert to inches
	x0_in = x0_fig * fig_w
	y0_in = y0_fig * fig_h
	w_ax_in = w_fig * fig_w
	h_ax_in = h_fig * fig_h
	# use same width as ax if not specified
	#if w_in is None:
	w_in = w_ax_in
	# new axes position in inches
	new_x0_in = x0_in + 0
	new_y0_in = y0_in - 0.2
	# convert back to figure coords
	new_x0 = new_x0_in / fig_w
	new_y0 = new_y0_in / fig_h
	new_w  = w_in / fig_w
	new_h  = 0.1 / fig_h
	cax = fig.fig.add_axes([new_x0, new_y0, new_w, new_h])
	cb = plt.colorbar(im, cax=cax, orientation='horizontal', extend=extend)
	cb.ax.tick_params(labelsize=fs-2)     # tick labels
	return cb

####################
# START
# Make some general initializations:
sub = subc(region=DREGION)
g = getg()


printname = {
	FLUX_VAR: 'SHF',
	#'egr': r'$\sigma_E$',
	'egr': r'Baroclinicity ($\sigma_E$)',
	'bvf': r'BVF ($N$)',
	'dvdz': r'dvdz',
	'sst': 'SST',
	'msl': 'SLP',
	'dtdy': 'dtdy',
	'sshf': 'SHF',
	'slhf': 'LHF',
	#'slhf+sshf': 'Fluxes',
	'tp': 'TP',
	'ecmwf': 'SEAS5',
	'era5': 'ERA5'
}

units = {
	FLUX_VAR: 'W m$^{-2}$', 
	'egr': 'day$^{-1}$',
	'dtdy': 'K deg$^{-1}$',
	'sst': 'K',
	'msl': 'hPa'
}

mapkw = {
	'dpi': 450, 
	'filetype': 'png'
}

plots = (

	'sst_maps', # Fig. 1
	'bias_maps', # Fig. 3
	'med_maps_new', # Fig. 4-6
	'skill_maps', # Figs. 2,7
	
)

if len(INITMONTHS) == 1 and not INITMONTHS[0] == 11:
	print('*'*20)
	print('*********** Check initmonth is not 11!')

def zscore(x):
	return (x - x.mean()) / x.std(ddof=1)

if 'skill_maps' in plots:

	sub = subc(region=DREGION)
	g = getg()
	lon, lat = g['lon'], g['lat']
	refmonths = [12, 1, 2]
	B = 10000
	#ts_len = 43*25
	ts_len = VALPERIOD[-1] - VALPERIOD[0] + 1
	nmember = 25
	nsamp = nmember*ts_len
	model = create_model('ecmwf')
	era5 = create_model('era5')

	variables = (
		FLUX_VAR, 
		'egr',
		#'tp',
		#'bvf',
	)

	lon_sub, lat_sub = sub['lon'], sub['lat']
	cv = np.linspace(-.4, .4, 21)
	cmap = plt.get_cmap('cmc.vik',len(cv)-1)
	boot_idx = None
	skill_boot = None
	sst_idx_mod = model.get_sst_index()              # shape (nyear*nmember,)
	print(sst_idx_mod.shape)
	nao_idx_mod = model.get_nao(months=refmonths)    # expect (nyear, nmember) or (nyear*nmember,)
	reanalysis = create_model('era5')
	sst_idx_rean = np.repeat(reanalysis.get_sst_index()[:,None], nmember, axis=1).ravel()        # (nyear,)
	#print(sst_idx_rean.shape)
	#print(sst_idx_rean[:3,:3])
	#sys.exit()
	nao_idx_rean = np.repeat(reanalysis.get_nao(months=refmonths)[:,None], nmember, axis=1).ravel()       # (nyear,)
	init = True

	# 43 samples per bootstrap, drawn from all (year,member) combos
	fig = SubplotFigure(
		aspectratio = 1,
		figw_inches = TWI/3,
		marginleft_inches = 0.55,
		margintop_inches = .24
	)
	np.random.seed(42)
	boot_idx = np.random.randint(0, nsamp, size=(B, ts_len))  # (B, 43)
	r_sst_nao_b = np.empty((B,))
	skill_b = np.empty((B,))
	for b in range(B):
		idx = boot_idx[b]                    # shape (43,)
		sst_mod_b = sst_idx_mod.ravel()[idx]
		nao_mod_b = nao_idx_mod.ravel()[idx]
		nao_rean_b = nao_idx_rean[idx]
		r_sst_nao_b[b] = pearsonr(nao_mod_b, sst_mod_b)[0]
		skill_b[b] = pearsonr(nao_mod_b, nao_rean_b)[0]
	#ax = fig.subplot(subplotcount, marginleft = fig.marginleft*7)
	rvalue, pvalue = pearsonr(r_sst_nao_b, skill_b)
	print(rvalue)
	ax = fig.subplot(0)
	#plt.figure()
	n_points = len(r_sst_nao_b)
	sample_size = 500	# adjust as you like
	rng = np.random.default_rng(42)		# fixed seed for reproducibility
	ix = rng.choice(n_points, size=sample_size, replace=False)

	plt.plot(
		r_sst_nao_b[ix],
		skill_b[ix],
	#plt.plot(r_sst_nao_b, skill_b, 
		'o', mec='#e2852e', mew=0.3, mfc='None', ms=4, alpha=1)
	pimp_axes(ax)
	fig.axtitle(r'$\hat{\tau}$ vs. $\hat{\rho}$ ($r=%.2f$)'%(rvalue), fontsize=fs-1)
	plt.xlabel(r'SST$-$NAO correlation ($\hat{\tau}$)', fontsize=fs-1)
	plt.ylabel(r'NAO skill ($\hat{\rho}$)', fontsize=fs-1)
	maxval = max(np.max(np.abs(r_sst_nao_b)), np.max(np.abs(skill_b))) * 1.15
	plt.xlim([-maxval, maxval])
	plt.ylim([-maxval, maxval])
	ax.xaxis.set_major_locator(MultipleLocator(0.3))
	ax.yaxis.set_major_locator(MultipleLocator(0.3))
	plt.plot([-maxval, maxval], [-maxval, maxval], 'k--', lw=0.6)
	draw_map_border(ax, zorder=102)
	savefig('scatter')

	nx = len(variables)
	if nx in [2,4]:
		xpos, ypos = 0.021, 0.961
	elif nx==3:
		xpos, ypos = 0.022, 0.962

	fig = SubplotFigure(
		aspectratio = sub['asp'] * 0.8,
		figw_inches = TWI*2./3.,
		#figw_inches = TWI,
		#figmarginleft_inches = 0.15,
		#title_height_inches = 0.24,
		kind = 'map',
		nx = nx,
		ny = 1,
		marginright_inches = 0.05,
		marginleft_inches = 0.08,
		margintop_inches = .24,
		marginbottom_inches = .43
	)
	subplotcount = 0


	for variable in variables:

		e = [
			'skill_map',
			variable,
			'%i-%i'%(VALPERIOD[0], VALPERIOD[-1]),
			'%i'%B
		]
		cachefile = '%s/%s'%(cachedir,'_'.join(e))
		try:
			res = loadpickle(cachefile)
		except:
			res = {}
			# Compute mediated effect in reanalysis:
			data = era5.get_seasonal_data(variable=variable, months=refmonths)	# (nyear,nmember,nlat,nlon)
			nyear = data.shape[0]
			data = data[np.ix_(range(nyear), [0], sub['I'], sub['J'])]
			ngrid = np.prod(data.shape[1:])
			x_raw = era5.get_sst_index().reshape(nyear)				# X
			y_raw = era5.get_nao(months=refmonths).reshape(nyear)		# Y (DJF NAO)
			Z_raw = data.reshape(nyear, ngrid)
			xs = np.asarray(zscore(x_raw))
			ys = np.asarray(zscore(y_raw))
			Zs = Z_raw.std(axis=0, keepdims=True, ddof=1)
			Zs[Zs == 0] = np.nan
			Z = (Z_raw - Z_raw.mean(axis=0, keepdims=True)) / Zs
			Z = np.asarray(Z)   # <-- absolutely essential
			r_xy = float((xs * ys).mean())
			r_xz = (xs[:, None] * Z).mean(axis=0)
			r_yz = (ys[:, None] * Z).mean(axis=0)
			den = 1.0 - r_xz**2
			den[den == 0] = np.nan
			beta = (r_yz - r_xy * r_xz) / den
			alpha = r_xz
			res['ie_rean'] = alpha * beta

			data = model.get_seasonal_data(variable=variable, months=refmonths)
			nyear, nmember = data.shape[:2]
			if not init:
				sst_idx_mod = model.get_sst_index()              # shape (nyear*nmember,)
				nao_idx_mod = model.get_nao(months=refmonths)    # expect (nyear, nmember) or (nyear*nmember,)
				reanalysis = create_model('era5')
				sst_idx_rean = np.repeat(reanalysis.get_sst_index()[:,None], nmember, axis=1).ravel()        # (nyear,)
				nao_idx_rean = np.repeat(reanalysis.get_nao(months=refmonths)[:,None], nmember, axis=1).ravel()       # (nyear,)
				init = True

			data = data[np.ix_(range(nyear), range(nmember), sub['I'], sub['J'])]

			nlat, nlon = data.shape[2:]
			ngrid = nlat * nlon
			nsamp = nyear * nmember

			# reshape model indices
			sst_mod = sst_idx_mod.reshape(nyear, nmember)
			nao_mod = nao_idx_mod.reshape(nyear, nmember)

			X_raw = sst_mod.reshape(nsamp)           # (nsamp,)
			Y_raw = nao_mod.reshape(nsamp)           # (nsamp,)
			Z_raw = data.reshape(nsamp, ngrid)       # (nsamp, ngrid)

			skill_boot = np.full(B, np.nan, dtype=np.float32)

			for b in range(B):
				idx = boot_idx[b]                    # shape (43,)

				nao_mod_samp = Y_raw[idx]           # model NAO for those (year,member)
				nao_rean_samp = nao_idx_rean[idx]  # ERA5 NAO for those years

				y_mod_s = zscore(nao_mod_samp)
				y_rean_s = zscore(nao_rean_samp)

				skill_boot[b] = np.nanmean(y_mod_s * y_rean_s)

			# now compute de-confounded IE for this variable for each bootstrap
			keys = ['actual','deconf','alpha_prime']
			ie_clean_boot = {key: np.full((B, ngrid), np.nan, dtype=np.float32) for key in keys}

			for b in range(B):

				idx = boot_idx[b]                    # (43,)
				xb = X_raw[idx]
				yb = Y_raw[idx]
				Zb = Z_raw[idx, :]                   # (43, ngrid)

				# standardise X, Y
				xs = zscore(xb)
				ys = zscore(yb)

				# standardise Z per grid point
				Zb_mean = np.nanmean(Zb, axis=0, keepdims=True)
				Zb_std = np.nanstd(Zb, axis=0, ddof=1, keepdims=True)
				Zb_std[Zb_std == 0] = np.nan
				Zbs = (Zb - Zb_mean) / Zb_std        # (43, ngrid)

				# correlations
				r_xy = np.nanmean(xs * ys)
				r_xz = np.nanmean(xs[:, None] * Zbs, axis=0)   # (ngrid,)
				r_yz = np.nanmean(ys[:, None] * Zbs, axis=0)   # (ngrid,)

				# beta: coef of Z in Y ~ X + Z
				den1 = 1.0 - r_xz * r_xz
				den1[den1 == 0] = np.nan
				beta = (r_yz - r_xy * r_xz) / den1

				ie_clean_boot['actual'][b, :] = r_xz * beta   # mediated effect

				# alpha_prime: coef of X in Z ~ X + Y
				den2 = 1.0 - r_xy * r_xy
				if den2 == 0:
					alpha_prime = np.full_like(r_xz, np.nan)
				else:
					alpha_prime = (r_xz - r_xy * r_yz) / den2
				ie_clean_boot['alpha_prime'][b, :] = alpha_prime  
				ie_clean_boot['deconf'][b, :] = alpha_prime * beta   # de-confounded mediated effect

			# correlation across bootstraps between de-confounded IE and NAO skill
			# normalise across B for each grid point
			for key, val in ie_clean_boot.items():

				ie_mean = np.nanmean(val, axis=0)
				ie_std = np.nanstd(val, axis=0, ddof=1)
				ie_std[ie_std == 0] = np.nan
				ie_norm = (val - ie_mean[None, :]) / ie_std[None, :]

				skill_mean = np.nanmean(skill_boot)
				skill_std = np.nanstd(skill_boot, ddof=1)
				skill_norm = (skill_boot - skill_mean) / skill_std

				corr_map = np.nanmean(ie_norm * skill_norm[:, None], axis=0)   # (ngrid,)
				res[f'corr_map_2d_{key}'] = corr_map.reshape(nlat, nlon)

				#print(B, ts_len)
				#sys.exit()
				z = 0.5 * np.log((1 + corr_map) / (1 - corr_map))
				sigma = 1 / np.sqrt(B - 3)
				pvals = 2 * (1 - norm.cdf(np.abs(z) / sigma))
				res[f'pvals_2d_{key}'] = pvals.reshape(nlat, nlon)
			savepickle(cachefile, res)

		# plot
		#plot_key = 'alpha_prime'
		plot_key = 'actual'
		#plot_key = 'deconf'
		ax = fig.subplot(subplotcount, proj=sub['proj'])
		ax.set_aspect('auto')
		im = plt.pcolormesh(
			# lon_sub, lat_sub, res['corr_map_2d_actual'],
			#lon_sub, lat_sub, res['corr_map_2d_deconf'],
			lon_sub, lat_sub, res[f'corr_map_2d_{plot_key}'],
            cmap=cmap, vmin=cv[0], vmax=cv[-1],
            shading='auto', transform=ccrs.PlateCarree()
		)
		if 0:
			mask_numeric = np.where(res[f'pvals_2d_{plot_key}'].ravel()>0.05, 1, np.nan)
			ax.contourf(lon_sub, lat_sub, mask_numeric.reshape(lat_sub.shape),
	            levels=[0.5, 1.5],       # one filled region
	            hatches=['////'],        # or '\\\\', 'xx', etc.
	            #linewidths=.5,
	            #hatches=['....'],        # or '\\\\', 'xx', etc.
	            colors='none',           # keep background visible
	            transform=ccrs.PlateCarree())
		else:
			#mask_sig = (res[f'pvals_2d_{plot_key}']<0.05).reshape(lat_sub.shape)
			mask_sig = (res[f'pvals_2d_{plot_key}']>0.05).reshape(lat_sub.shape)
			ax.plot(lon_sub[mask_sig], lat_sub[mask_sig], 'o', mew=0, mfc='k', ms=0.7, zorder=99)

		# Contours of IE in ERA5:
		a = res['ie_rean'].reshape(lat_sub.shape)
		# Smooth the field before contouring
		a = gaussian_filter(a, sigma=1.0)   # try sigma ∈ [0.5, 1.5]
		lw = .6
		color = 'w'
		sp = 0.1
		plt.contour(lon_sub, lat_sub, a,
	    	levels=np.arange(sp,1,sp),
			colors=color, linestyles='solid', linewidths=lw,
			transform=ccrs.PlateCarree(), zorder=100)
		plt.contour(lon_sub, lat_sub, a,
	    	levels=np.arange(-1.,0,sp),
			colors=color, linestyles='dashed', linewidths=lw,
			transform=ccrs.PlateCarree(), zorder=100)

		# mask_sig = res[f'sig_{field}'].reshape(lat.shape)
		# ax.plot(lon[mask_sig], lat[mask_sig], 'o', mew=0, mfc='k', ms=0.7, zorder=99)
		draw_letter(ax, xpos, ypos, subplotcount, zorder=1004)
		# mask_sig = (res['pvals_2d']<0.05)
		# ax.plot(lon[mask_sig], lat[mask_sig], 'o', mew=0, mfc='k', ms=0.7, zorder=99)
		fig.axtitle(r'$r(\hat{\rho}, \hat{\alpha} \hat{\beta})$ for %s'%(printname[variable]), fontsize=fs-1)
		#fig.axtitle(printname[variable], fontsize=fs-1)
		drawfeatures(ax)
		draw_map_border(ax, zorder=102)
		cb = plot_cbar_below(fig, ax, im)

		subplotcount += 1

	savefig(f'skill_maps_{mstr}')


if 'bias_maps' in plots:
	lag = 1
	variables = (
		#'ratio',
		'sst',
		FLUX_VAR,
		'egr',
		#'dtdy',
		'msl',
	)
	#medvar = variables[1]
	bias = {}
	era5 = create_model('era5')
	seas5 = create_model('ecmwf')
	bias_cv = {
		'sst': np.linspace(-4,4.1,21),
		'msl': np.linspace(-2,2.1,21),
		'dtdy': np.linspace(-.5,.5,21),
		FLUX_VAR: np.linspace(-120,120,25),
		'egr': np.linspace(-0.15,0.15,31)
	}
	clim_cv = {
		'sst': np.linspace(270,300,31),
		'msl': np.linspace(990,1030,21),
		'dtdy': np.linspace(0,5,21),
		FLUX_VAR: np.linspace(0,400,21),
		'egr': np.linspace(0,1,21)
	}
	lon, lat = sub['lon'], sub['lat']
	show_climo = True
	#B = 333
	nx = len(variables)
	fig = SubplotFigure(
		aspectratio = sub['asp'] * 0.8,
		figw_inches = TWI,
		kind = 'map',
		nx = nx,
		figmarginleft_inches = 0.2,
		margintop_inches = 0.22,
		marginright_inches = 0.1,
		ny = 1 + int(show_climo),
		marginbottom_inches = .42
	)
	subplotcount = 0
	xpos,ypos = 0.03, 0.947
	Z = {}
	for variable in variables:
		ax = fig.subplot(subplotcount,proj=sub['proj'])
		ax.set_aspect('auto')
		months = ([11] if variable=='sst' else [12,1,2])
		if variable == 'ratio':
			cv = np.linspace(-.3,.3,21)
			ngrid = np.prod(sub['lat'].shape)
			IE = {}
			for modelname in ['era5','ecmwf']:
				model = create_model(modelname)
				#ie = np.empty((B*len(months), ngrid))
				ie = np.empty((len(months), ngrid))
				count = 0
				for m in months:
					data = model.get_seasonal_data(variable=medvar, months=[m])
					nyear, nmember = data.shape[:2]
					nsamp = nyear * nmember
					sst_idx = model.get_sst_index(refmonth=m, lag=lag).reshape(nsamp)
					nao_idx = model.get_nao(months=[m]).reshape(nsamp)
					# Subselect region and flatten
					data = data[np.ix_(range(nyear), range(nmember), sub['I'], sub['J'])]
					data2 = data.reshape(nsamp, ngrid)
					data2 -= np.mean(data2, axis=0, keepdims=True)
					_, _, a, b = regress_all(nao_idx, sst_idx, data2)
					ie[count]   = a * b
					count += 1
				IE[modelname] = np.mean(ie, axis=0).reshape(lat.shape)
			z = IE['ecmwf'] - IE['era5']
		else:
			obs  = era5.get_seasonal_data(variable=variable, months=months) # (ny,nmem,nlat,nlon)
			mod  = seas5.get_seasonal_data(variable=variable, months=months) # (ny,nmem,nlat,nlon)
			climo = np.mean(obs[:,0,:,:], axis=0)[sub['ix']]
			bias = mod.mean(axis=1) - obs[:,0,:,:] # (ny,nlat,nlon)
			bias = bias[np.ix_(range(bias.shape[0]),sub['I'],sub['J'])]
			z = bias.mean(axis=0)
		if 0 and not variable=='sst':
			ref_region = (EGR if variable=='egr' else SPG)
			bb = CBOXES[ref_region]
			mask_spg = (lat >= bb[0]) & (lat <= bb[1]) & (lon >= bb[2]) & (lon <= bb[3])
			mask_spg_flat = mask_spg.ravel()
			w2d = np.cos(np.deg2rad(lat))
			w_flat = w2d.ravel()
			num = np.nansum(z.ravel()[mask_spg_flat] * w_flat[mask_spg_flat])
			den = np.nansum(w_flat[mask_spg_flat])
			spg_bias = num / den

		t = '%s %s (%s)'%(
			('November' if variable=='sst' else 'DJF'),
			printname[variable],
			units[variable]
		)

		dregion = None

		if show_climo:
			cv = clim_cv[variable]
			#if variable in ['egr','sst']:
			#cmap = plt.get_cmap('Reds',len(cv)-1)
			cmap = plt.get_cmap('cmc.lajolla_r',len(cv)-1)
			#else:
			#	cmap = plt.get_cmap('RdBu_r',len(cv)-1)
			im = ax.pcolormesh(lon,lat,climo,cmap=cmap,vmin=cv[0],vmax=cv[-1],shading='auto',transform=ccrs.PlateCarree())
			#im = ax.contourf(lon,lat,climo,cv,cmap=cmap,vmin=cv[0],vmax=cv[-1],transform=ccrs.PlateCarree())
			if subplotcount==0:
				fig.axylab('ERA5 climatology', fontsize = fs-1)
			drawfeatures(ax)
			fig.axtitle(t,fontsize = fs-1)		
			draw_letter(ax, xpos, ypos, subplotcount, zorder=101)
			draw_map_border(ax, zorder=102)
			cb = plot_cbar_below(fig, ax, im)
			# if variable in ['sst']:
			# 	#print('haha')
			# 	cb.ax.xaxis.set_major_locator(MultipleLocator(5.0))
			if dregion is not None:
				plot_box(ax, dregion)
			ax = fig.subplot(subplotcount+nx,proj=sub['proj'])
			#ax = fig.subplot(subplotcount+1,proj=sub['proj'])
			ax.set_aspect('auto')
			if dregion is not None:
				plot_box(ax, dregion)

		cv = bias_cv[variable]
		cmap = plt.get_cmap('cmc.vik',len(cv)-1)
		im = ax.pcolormesh(lon,lat,z,cmap=cmap,vmin=cv[0],vmax=cv[-1],shading='auto',transform=ccrs.PlateCarree())
		Z[variable] = z
		if variable == 'ratio':
			fig.axtitle(r'$\Delta \alpha \beta$ (SEAS5$-$ERA5)', fontsize = fs-1)
		elif variable == 'msl':
			def nearest_point(lat_arr, lon_arr, lat0, lon0):
				lon0_wrapped = lon0
				# compute squared distance on the lat/lon grid
				dist2 = (lat_arr - lat0)**2 + (lon_arr - lon0_wrapped)**2
				j,i = np.unravel_index(np.argmin(dist2), dist2.shape)
				return j,i
			# coordinates of the two centres of action
			lat_iceland, lon_iceland = 65.1, -22.7   # Stykkishólmur, Iceland
			lat_azores,  lon_azores  = 37.7, -25.7   # Ponta Delgada, Azores

			# get nearest grid cells
			j_ic, i_ic = nearest_point(lat, lon, lat_iceland, lon_iceland)
			j_az, i_az = nearest_point(lat, lon, lat_azores,  lon_azores)

			# extract mean-state SLP bias (SEAS5 - ERA5) at each site
			bias_iceland = z[j_ic, i_ic]   # hPa
			bias_azores  = z[j_az, i_az]   # hPa

			# NAO-like dipole bias: south minus north
			nao_bias = bias_azores - bias_iceland  # hPa

			print("Mean SLP bias at Iceland (SEAS5-ERA5):", bias_iceland, "hPa")
			print("Mean SLP bias at Azores  (SEAS5-ERA5):", bias_azores,  "hPa")
			print("Approximate NAO-like mean-state bias (Azores - Iceland):", nao_bias, "hPa")
		else:
			if subplotcount==0:
				fig.axylab('SEAS5 bias', fontsize = fs-1)
		fig.axtitle(t,fontsize = fs-1)		
		drawfeatures(ax)
		draw_letter(ax, xpos, ypos, subplotcount + int(show_climo)*nx, zorder=101)
		draw_map_border(ax, zorder=102)

		plot_cbar_below(fig, ax, im)

		subplotcount += 1

	savefig('bias_maps_%s'%('_'.join(['%i'%i for i in INITMONTHS])), **mapkw)




if 'med_maps_new' in plots:

	B = 10000

	titles = {'chi': r'$\chi$'}
	titles['ie'] = r'$\mu$'
	titles['ie'] = r'$\hat{\alpha} \hat{\beta}$'
	titles['ie_rev'] = r'IE_rev'
	titles['r_xz_y'] = r'$r_{X,Z|Y}$ (contours: SLP)'
	titles['r_yz'] = r'$r_{Y,Z}$'
	titles['r_yz_x'] = r'r_yz_x'
	titles['r_xy_z'] = r'r_xy_z'
	titles['alpha'] = r'$\hat{\alpha}$'
	titles['beta'] = r'$\hat{\beta}$'
	#titles['alpha_prime'] = r"$\hat{\alpha'}$ (contours: SLP)"
	titles['alpha_prime'] = r"$\widehat{\alpha'}$"
	titles['alpha_double_prime'] = r"$\widehat{\alpha'}$"
	titles['gamma'] = r"$\gamma'$"
	titles['fai'] = r"$\hat{\beta} / \hat{\gamma} - 1$"
	titles['ie_cleaned'] = r"$\widehat{\alpha'} \hat{\beta}$"
	titles['strict'] = r'$\mathrm{sign}(r_{X,Z|Y} \times r_{Z,Y|X})$'
	cvs = {
		'chi': np.linspace(0, 1, 11),
		'ie_actual': np.linspace(-.5, .5, 21)
	}
	cvs['ie'] = np.linspace(-.5, .5, 21)		# ERA5: μ = IE / τ
	cvs['ie_cleaned'] = cvs['ie']
	cvs['ie_double_cleaned'] = cvs['ie']
	cvs['alpha'] = np.linspace(-1., 1., 21)		# ERA5: μ = IE / τ
	cvs['r_xz_y'] = np.linspace(-.5, .5, 21)		# ERA5: μ = IE / τ
	cvs['r_yz_x'] = np.linspace(-1, 1, 21)		# ERA5: μ = IE / τ
	cvs['r_yz'] = np.linspace(-1, 1, 21)		# ERA5: μ = IE / τ
	cvs['r_xy_z'] = np.linspace(-.5, .5, 21)		# ERA5: μ = IE / τ
	cvs['strict'] = np.linspace(-.5, .5, 21)
	cvs['beta'] = np.linspace(-1., 1., 21)
	cvs['alpha_prime'] = cvs['alpha']
	cvs['alpha_double_prime'] = cvs['alpha']
	cvs['gamma'] = cvs['beta']
	cvs['fai'] = np.linspace(-.4, .4, 17)

	modelnames = (
		'era5', 
		#'ecmwf',
	)
	refmonths = [12, 1, 2]
	#refmonths = [2]
	lon, lat = sub['lon'], sub['lat']
	variables = (
		FLUX_VAR,
		#'egr', 
		#'dtdy',
		#'msl',
		#'sst',
	)
	reverse = False
	def zscore1d(a):
		m = a.mean()
		s = a.std(ddof=1)
		return (a - m) / s

	variables = (
		#'sst',
		FLUX_VAR,
		'egr',
		#'tp',
	)

	figprops = []

	# Fig. 6
	if 1:
		panels = []
		for modelname in (
			'era5',
			'ecmwf',
		):
			panels.extend([
				{'modelname': modelname, 'field': 'alpha_prime', 'variable': 'sst', 'contour_variable': 'msl',
				'title': r"$\widehat{\alpha'}$ for SST/SLP"}
			])
			for variable in variables:
				if 0:
					panels.extend([
						{
							'modelname': modelname, 
							'field': 'alpha_prime', 
							'variable': variable, 
							'title': r"$\widehat{\alpha'}$ for %s"%(printname[variable])}
					])
				else:
					panels.extend([
						{
							'modelname': modelname, 
							'field': 'ie_cleaned', 
							#'field': 'ie_double_cleaned', 
							'variable': variable, 
							'title': r"$\widehat{\alpha'} \hat{\beta}$ for %s"%(printname[variable])}
					])
		filename = f'sst-forced_{mstr}'
		if len(refmonths)==1:
			filename += '_%02d'%(refmonths[0])
		figprops.append({
			'filename': filename,
			'nx': 3,
			'panels': panels,
			'title': r"SST-forced effect ($\widehat{\alpha'}$) and mediated effect ($\widehat{\alpha'} \hat{\beta}$)"
		})

	# Figs. 4, 5
	if 1:
		for variable in variables:
			panels = []
			for modelname in (
				'era5',
				'ecmwf',
			):
				panels.extend([
					{'modelname': modelname, 'field': 'alpha', 'variable': variable},#, 'contour_variable': ('msl' if variable=='sst' else None)},
					{'modelname': modelname, 'field': 'beta', 'variable': variable},#, 'contour_variable': ('msl' if variable=='sst' else None)},
					{'modelname': modelname, 'field': 'ie', 'variable': variable}#, 'contour_variable': ('msl' if variable=='sst' else None)},
				])
			filename = f'params_{variable}_{mstr}'
			if len(refmonths)==1:
				filename += '_%02d'%(refmonths[0])
			figprops.append({
				'nx': 3,
				'filename': filename,
				'panels': panels,
				'title': f'Sample parameters for {printname[variable]}'
			})

	for props in figprops:

		figtitle = props['title']
		panels = props['panels']
		try:
			ylab = props['ylab']
		except:
			ylab = True
		try:
			nx = props['nx']
		except:
			nx = min(3,len(panels))
		try:
			figw_inches = props['figw_inches']
		except:
			figw_inches = np.min([TWI, TWI*nx/3.])
		ny = int(len(panels)/float(nx))
		#ny = len(modelnames)

		if nx in [2,4]:
			#xpos, ypos = 0.029, 0.95
			xpos, ypos = 0.03, 0.95
		elif nx==3:
			xpos, ypos = 0.022, 0.962


		fig = SubplotFigure(
			aspectratio = sub['asp'] * 0.8,
			figw_inches = figw_inches,
			figmarginleft_inches = int(ylab) * 0.15,
			title_height_inches = 0.24,
			kind = 'map',
			#nx = len(plot_fields),
			nx = nx,
			ny = ny,
			marginright_inches = 0.05,
			marginleft_inches = 0.05,
			margintop_inches = .2,
			marginbottom_inches = .43
		)
		fig.title(figtitle, fontsize=fs)
		subplotcount = 0

		def compute_stats(variable, modelname):
			#siglevel = (10 if modelname=='era5' else 5)
			siglevel = 5
			fair = True
			cleaned = True
			e = [
				'med_maps_new',
				modelname,
				variable,
				'+'.join('%02d'% i for i in refmonths),
				'dregion_'+'_'.join('%.1f'% i for i in CBOXES[DREGION]),
				'%i'%B
			]
			append_to_e(e)
			if modelname=='ecmwf' and ENSEMBLE_MEAN:
				e.append('em')
			if not siglevel == 5:
				e.append('%i'%siglevel)
			if modelname=='ecmwf' and fair:
				e.append('fair')
			if cleaned:
				e.append('cleaned')
			cachefile = '%s/%s'%(cachedir,'_'.join(e))
			try:
				res = loadpickle(cachefile)
			except:
				model = create_model(modelname)
				res = {}
				# ---- Load and flatten time-series ----
				data = model.get_seasonal_data(variable=variable, months=refmonths)	# (nyear,nmember,nlat,nlon)
				nyear, nmember = data.shape[:2]
				nsamp = nyear * nmember
				# subselect region and flatten mediator field
				data = data[np.ix_(range(nyear), range(nmember), sub['I'], sub['J'])]
				ngrid = data.shape[2] * data.shape[3]

				# New code to include NOV NAO:
				x_raw = model.get_sst_index().reshape(nsamp)				# X
				y_raw = model.get_nao(months=refmonths).reshape(nsamp)		# Y (DJF NAO)
				n_raw = model.get_nao(months=SST_MONTHS).reshape(nsamp)		# N (Nov NAO)
				Z_raw = data.reshape(nsamp, ngrid)

				# --- Standardised 1D predictors (force to plain ndarray) ---
				xs = np.asarray(zscore1d(x_raw))
				ys = np.asarray(zscore1d(y_raw))
				ns = np.asarray(zscore1d(n_raw))

				# --- Z as plain ndarray (nsamp, ngrid) ---
				Zm = Z_raw.mean(axis=0, keepdims=True)
				Zs = Z_raw.std(axis=0, keepdims=True, ddof=1)
				Zs[Zs == 0] = np.nan
				Z = (Z_raw - Zm) / Zs
				Z = np.asarray(Z)   # <-- absolutely essential

				# --- Two-predictor case stays unchanged ---
				r_xy = float((xs * ys).mean())
				r_xz = (xs[:, None] * Z).mean(axis=0)
				r_yz = (ys[:, None] * Z).mean(axis=0)

				den = 1.0 - r_xz**2
				den[den == 0] = np.nan
				res['beta']   = (r_yz - r_xy * r_xz) / den
				res['tau_Z']  = (r_xy - r_xz * r_yz) / den

				den2 = 1.0 - r_xy * r_xy
				res['alpha_prime'] = (r_xz - r_xy * r_yz) / den2
				res['gamma']       = (r_yz - r_xy * r_xz) / den2
				res['alpha']       = r_xz

				# --- Three-predictor case: Z ~ X + Y + N ---
				P = np.column_stack([xs, ys, ns])  # now all plain ndarrays

				PtP = P.T @ P                      # shape (3,3)
				PtP_inv = np.linalg.inv(PtP)
				coef_mat = PtP_inv @ (P.T @ Z)     # shape (3, ngrid)

				res['alpha_double_prime'] = coef_mat[0, :]
				res['gamma_prime']        = coef_mat[1, :]
				res['delta']              = coef_mat[2, :]


				# ---- Bootstrapping for significance (no persistent giant arrays) ----
				boot_n = nyear
				if modelname=='ecmwf' and not fair:
					boot_n = nsamp
				np.random.seed(42)	# reproducible RNG outside loops
				boot_idx = np.random.randint(0, nsamp, size=(B, boot_n))  # (B, nsamp)
				boot = {key: np.full((B, ngrid), np.nan, dtype=np.float32) for key in res}
				for b in range(B):
					idx = boot_idx[b]

					# New to include NOV NAO:
					# standardise predictors
					xb = np.asarray(np.ma.filled(zscore1d(x_raw[idx]), np.nan))
					yb = np.asarray(np.ma.filled(zscore1d(y_raw[idx]), np.nan))
					nb = np.asarray(np.ma.filled(zscore1d(n_raw[idx]), np.nan))

					Zb = Z_raw[idx, :].astype(float)
					Zb = (Zb - Zb.mean(axis=0)) / Zb.std(axis=0, ddof=1)

					# pairwise predictor correlations
					r_xy = float((xb * yb).mean())
					r_xn = float((xb * nb).mean())
					r_yn = float((yb * nb).mean())

					# correlations with Z (per grid point)
					r_xz = np.asarray((xb[:, None] * Zb).mean(axis=0))
					r_yz = np.asarray((yb[:, None] * Zb).mean(axis=0))
					r_nz = np.asarray((nb[:, None] * Zb).mean(axis=0))

					# --- 2-predictor mediation (as before) ---
					den = 1.0 - r_xz * r_xz
					den[den == 0] = np.nan
					boot['beta'][b, :]  = (r_yz - r_xy * r_xz) / den
					boot['tau_Z'][b, :] = (r_xy - r_xz * r_yz) / den

					den2 = 1.0 - r_xy * r_xy
					boot['alpha_prime'][b, :] = (r_xz - r_xy * r_yz) / den2
					boot['gamma'][b, :]       = (r_yz - r_xy * r_xz) / den2
					boot['alpha'][b, :]       = r_xz

					# --- 3-predictor regression Z ~ X + Y + N ---
					R_pred = np.array([
					    [1.0,  r_xy, r_xn],
					    [r_xy, 1.0,  r_yn],
					    [r_xn, r_yn, 1.0]
					], float)

					R_inv = np.linalg.inv(R_pred)

					rPZ = np.vstack([r_xz, r_yz, r_nz]).astype(float)

					coefs = R_inv @ rPZ

					boot['alpha_double_prime'][b, :] = coefs[0, :]
					boot['gamma_prime'][b, :]        = coefs[1, :]
					boot['delta'][b, :]              = coefs[2, :]


				#sig = {}
				res['ie'] = res['alpha'] * res['beta']
				boot['ie'] = boot['alpha'] * boot['beta']
				res['fai'] = res['beta'] / res['gamma'] - 1 
				boot['fai'] = boot['beta'] / boot['gamma'] - 1
				res['ie_cleaned'] = res['alpha_prime'] * res['beta']
				boot['ie_cleaned'] = boot['alpha_prime'] * boot['beta']
				res['ie_double_cleaned'] = res['alpha_double_prime'] * res['beta']
				boot['ie_double_cleaned'] = boot['alpha_double_prime'] * boot['beta']
				res['ratio'] = res['gamma'] / res['beta']
				boot['ratio'] = boot['gamma'] / boot['beta']
				res['ratio_new'] = res['alpha_prime'] / res['alpha']
				boot['ratio_new'] = boot['alpha_prime'] / boot['alpha']
				#boot['ratio_new'] = boot['alpha_prime'] / res['alpha']
				res['ratio_double'] = res['gamma_prime'] / res['beta']
				boot['ratio_double'] = boot['gamma_prime'] / boot['beta']
				res['ratio_a'] = res['alpha_prime'] / res['alpha']
				boot['ratio_a'] = boot['alpha_prime'] / boot['alpha']
				for key in boot.keys():
					if 'ratio_new' in key:
						#res[f'sig_{key}'] = np.nanpercentile(boot[key], 100.-siglevel, axis=0) < .5
						res[f'sig_{key}'] = np.nanpercentile(boot[key], siglevel, axis=0) > 0
						#res[f'sig_{key}'] = np.nanpercentile(boot[key], 100.-siglevel, axis=0) < 0
						#res[f'sig_{key}'] = res[key] < 0.5
						#res[f'sig_{key}'] = np.nanpercentile(boot[key], siglevel, axis=0) < 0
					elif 'ratio' in key:
						res[f'sig_{key}'] = np.nanpercentile(boot[key], siglevel, axis=0) > 1
						#res[f'sig_{key}'] = np.nanpercentile(boot[key], siglevel, axis=0) > .5
					else:
						lo = np.nanpercentile(boot[key], siglevel/2., axis=0)
						hi = np.nanpercentile(boot[key], 100.-siglevel/2., axis=0)
						res[f'sig_{key}'] = (lo * hi) > 0	# True where CI excludes 0

				savepickle(cachefile, res)
			return res


		for panel in panels:

			modelname = panel['modelname']
			variable = panel['variable']
			res = compute_stats(variable,modelname)
			field = panel['field']
			try:
				res_contour = compute_stats(panel['contour_variable'],modelname)
			except:
				res_contour = None

			ax = fig.subplot(subplotcount, proj=sub['proj'])
			ax.set_aspect('auto')

			if 0 and field=='gamma':
				#a_plot = res[field] - res['beta']
				a_plot = res['beta']/res[field]
				#a_plot[res[field]<1e-6] = np.nan
				#a_plot = 1/res[field] - res['beta']
			else:
				a_plot = res[field]

			cv = cvs[field]
			cmap = plt.get_cmap('cmc.vik', len(cv)-1)

			im = plt.pcolormesh(lon, lat, a_plot.reshape(lat.shape),
			                    cmap=cmap, vmin=cv[0], vmax=cv[-1],
			                    shading='auto', transform=ccrs.PlateCarree())

			mask_numeric = None
			if 1 and field in ['ie_cleaned','ie_double_cleaned']:
				#sig_key = 'sig_ratio'
				sig_key = 'sig_ratio_new'
				if 'double' in field:
					sig_key += '_double'
				mask_sig = res[sig_key].reshape(lat.shape)
				ax.plot(lon[mask_sig], lat[mask_sig], 'o', mew=0, mfc='k', ms=0.7, zorder=99)
			mask_sig = res[f'sig_{field}'].reshape(lat.shape)
			ax.plot(lon[mask_sig], lat[mask_sig], 'o', mew=0, mfc='k', ms=0.7, zorder=99)

			if mask_numeric is not None:
				ax.contourf(lon, lat, mask_numeric.reshape(lat.shape),
		            levels=[0.5, 1.5],       # one filled region
		            hatches=['////'],        # or '\\\\', 'xx', etc.
		            #linewidths=.5,
		            #hatches=['....'],        # or '\\\\', 'xx', etc.
		            colors='none',           # keep background visible
		            transform=ccrs.PlateCarree())


			drawfeatures(ax)
			draw_map_border(ax, zorder=102)

			# Draw SLP contours
			if res_contour is not None:
				a = res_contour[field].reshape(lat.shape)
				lw = .5
				color = 'w'
				sp = 0.1
				plt.contour(lon, lat, a,
			    	levels=np.arange(sp,1,sp),
					colors=color, linestyles='solid', linewidths=lw,
					transform=ccrs.PlateCarree(), zorder=1001)
				plt.contour(lon, lat, a,
			    	levels=np.arange(-1.,0,sp),
					colors=color, linestyles='dashed', linewidths=lw,
					transform=ccrs.PlateCarree(), zorder=1001)

			if nx*ny>1:
				draw_letter(ax, xpos, ypos, subplotcount, zorder=1004)

			try:
				title = panel['title']
			except:
				if field in ['ie_cleaned','gamma','fai']:
					title = f"{printname[variable]}"
				elif field == 'alpha_prime':
					title = f"{('ERA5' if modelname=='era5' else 'SEAS5')}"
				else:
					title = f"{titles[field]}"
			fig.axtitle(title, fontsize=fs)
			if ylab and subplotcount%nx==0:
				fig.axylab(('ERA5' if modelname=='era5' else 'SEAS5'), fontsize=fs-1)
			cb = plot_cbar_below(fig, ax, im)
			if cv[-1] - cv[0] < .8:
				cb.ax.xaxis.set_major_locator(MultipleLocator(0.1))
			elif cv[-1] - cv[0] <= 1.5:
				cb.ax.xaxis.set_major_locator(MultipleLocator(0.2))
			else:
				cb.ax.xaxis.set_major_locator(MultipleLocator(0.5))

			subplotcount += 1
		try:
			filename = props['filename']
		except:
			filename = '_'.join((
				panels[0]['variable'],
				','.join(['%i'%i for i in INITMONTHS])
			))
		savefig(filename, **mapkw)





if 'sst_maps' in plots:
	sub_sst = subc(region = SSTREGION)
	lon, lat = sub_sst['lon'], sub_sst['lat']
	cv = np.arange(-.45,.46,.05)
	cv_msl = np.arange(-20,21,1)
	cmap = plt.get_cmap('cmc.vik',len(cv)-1)
	B = 10000
	xpos, ypos = 0.016, 0.98
	fig = SubplotFigure(
		aspectratio = sub_sst['asp'] * 0.8,
		#figw_inches = 3.17,
		nx = 3,
		add_lettering = True,
		figmarginleft_inches = -0.37,
		marginleft_inches = 0.45,
		marginbottom_inches = 0.42,
		margintop_inches = 0.24
		#nx = len(refmonths)
	)
	subplotcount = 0
	nao_idx = {}
	sst_idx = {}
	nao_idx_raw = {}
	for modelname in ['era5','ecmwf']:
		model = create_model(modelname)
		sst_tm1 = model.get_seasonal_data(variable = 'sst', months=SST_MONTHS)
		nao_raw = model.get_nao(months = NAO_MONTHS).reshape(sst_tm1.shape[:2])
		nao_t = zscore(np.mean(nao_raw,axis=1).ravel())
		sst_raw = model.get_sst_index().reshape(sst_tm1.shape[:2])
		nao_idx_raw[modelname] = nao_raw
		sst_t = zscore(np.mean(sst_raw,axis=1).ravel())
		print(modelname, 'Raw correlation:',pearsonr(nao_raw.ravel(),sst_raw.ravel()))
		if modelname=='era5':
			sst_tm1 = np.mean(sst_tm1, axis=1)
			sst_tm1 = sst_tm1[np.ix_(range(sst_tm1.shape[0]),sub_sst['I'],sub_sst['J'])]
			sst_tm1 -= np.mean(sst_tm1, axis=0, keepdims=True)
			sst_map = np.tensordot(nao_t, sst_tm1, axes=(0, 0)) / len(nao_t)	# (nlat, nlon)
			msl = model.get_seasonal_data(variable = 'msl', months=NAO_MONTHS) # / 100
			msl = np.mean(msl, axis=1)
			msl = msl[np.ix_(range(msl.shape[0]),sub_sst['I'],sub_sst['J'])]
			msl -= np.mean(msl, axis=0, keepdims=True)
			msl_map = np.tensordot(nao_t, msl, axes=(0, 0)) / len(nao_t)	# (nlat, nlon)

			nlat, nlon = sst_tm1.shape[1:]
			nsamp = sst_tm1.shape[0]
			ngrid = nlat * nlon
			sst_flat = sst_tm1.reshape(nsamp, ngrid)

			# Bootstrap arrays
			np.random.seed(42)        # reproducibility
			boot_idx = np.random.randint(0, nsamp, size=(B, nsamp))
			bs_sst = np.empty((B, ngrid))

			for b in range(B):
				idx = boot_idx[b]
				nao_b = nao_t[idx]
				bs_sst[b, :] = nao_b @ sst_flat[idx, :] / nsamp

			# Significance masks (95% CI not including 0)
			sst_sig = (np.percentile(bs_sst, 2.5, axis=0) *
			           np.percentile(bs_sst, 97.5, axis=0)) > 0
			sst_sig = sst_sig.reshape(nlat, nlon)
			ax = fig.subplot(subplotcount,proj=sub_sst['proj'], offsetx_inches=0.4, offsety_inches=0.1)
			ax.set_aspect('auto')
			im = plt.pcolormesh(lon,lat,sst_map,cmap=cmap,vmin=cv[0],vmax=cv[-1],shading='auto',transform=ccrs.PlateCarree())
			ax.plot(lon[sst_sig], lat[sst_sig], 'o', mew=0, mfc='k', ms=0.8)
			# choose contour levels
			levels = cv_msl  # e.g. np.linspace(-2, 2, 11)
			# Positive levels only
			pos_levels = [lev for lev in levels if lev > 0]
			print(np.percentile(msl_map.ravel(), [0,10,50,90,100]))
			if pos_levels:
			    plt.contour(lon, lat, msl_map,
			                levels=pos_levels,
			                colors='k', linestyles='solid', linewidths=0.7,
			                transform=ccrs.PlateCarree(), zorder=1001)
			# Negative levels only
			neg_levels = [lev for lev in levels if lev < 0]
			if neg_levels:
			    plt.contour(lon,lat, msl_map,
			                levels=neg_levels,
			                colors='k', linestyles='dashed', linewidths=0.7,
			                transform=ccrs.PlateCarree(), zorder=1001)
			drawfeatures(ax)
			draw_map_border(ax)
			plot_cbar_below(fig, ax, im)
			fig.axtitle('ERA5 SST/SLP onto NAO', fontsize=fs-1)
			subplotcount += 1
		ax = fig.subplot(subplotcount, offsetx_inches=0.4, offsety_inches=0.1)
		years = range(VALPERIOD[0], VALPERIOD[-1]+1)
		nao_idx[modelname] = nao_t
		sst_idx[modelname] = sst_t
		lw = 1.2
		plt.plot(years, nao_t, label='NAO', linewidth=lw)
		plt.plot(years, sst_t, label='SST', linewidth=lw)
		pimp_axes(ax)
		plt.xlabel('Year', fontsize=fs-1)
		plt.ylabel('Index value (SD)', fontsize=fs-1)
		plt.ylim([-3.4,3.4])
		rvalue, pvalue = pearsonr(nao_t, sst_t)
		print('Corr(nao_t,sst_t):', rvalue, pvalue)
		if 0:
			for j, year in enumerate(years):
				print(year, nao_t[j], sst_t[j])
		fig.axtitle(r'%s ($%s=%.2f$)'%(
			('SEAS5' if modelname=='ecmwf' else 'ERA5'),
			(r'\hat{\tau}' if modelname=='era5' else r'\bar{\tau}'),
			rvalue), fontsize=fs-1)
		plt.legend(loc='upper right', ncol = 2, handlelength=0.9, handletextpad=0.3, borderpad=0.3, columnspacing=0.6, prop={'size':fs-3})
		showgridlines()
		subplotcount += 1

	savefig('sst_maps_%s'%('_'.join(['%i'%i for i in INITMONTHS])), **mapkw)
	print('NAO corr. ERA5/SEAS5:', pearsonr(nao_idx['era5'], nao_idx['ecmwf']))
	nao_idx_rean = np.repeat(nao_idx_raw['era5'][:,None], 25, axis=1).ravel()
	nao_idx_mod = nao_idx_raw['ecmwf'].ravel()
	print('Raw NAO corr. ERA5/SEAS5:', pearsonr(nao_idx_rean, nao_idx_mod))
	print('SST corr. ERA5/SEAS5:', pearsonr(sst_idx['era5'], sst_idx['ecmwf']))



if not VALPERIOD == [1981,2023]:
	print('**** VALPERIOD:', VALPERIOD)

plt.show()





