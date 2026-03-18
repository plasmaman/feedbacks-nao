
import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.textpath import TextPath
from matplotlib.colors import ListedColormap
from matplotlib.colorbar import ColorbarBase
from matplotlib.colors import Normalize

LETTERS = 'abcdefghijklmnopqrstuvxyzabcdefghijklmnopqrstuvxyz'

class SubplotFigureBase(object):

	def __init__(self, 
		figw_inches = None, 
		figh_inches = None,
		nx = None, 
		ny = None, 
		nbr_of_panels = None,
		kind = None,
		axw_inches = None,
		axh_inches = None, 
		aspectratio = 1.0,
		aspectratiobyrow = None,
		figmarginleft_inches = 0.0,
		addcolorbar = False,
		cbar_height_inches = 0,
		cbar_width_inches = 0,
		cbar_bottompadding_inches = 0,
		cbar_rightpadding_inches = 0,
		cbar_toppadding_inches = 0,
		cbar_leftpadding_inches = 0,
		cbar_width_percent = None,
		nbr_of_cbars = 1,
		title_height_inches = 0,
		base_fontsize = None,
		add_lettering = False,
		letter_format = '%s',
		#letter_format = '(%s)',
		letter_fontsize = None,
		#letter_fontweight = 'normal',
		letter_fontweight = 'bold',
		letter_offsetx_inches = None, 
		letter_offsety_inches = None,
		letter_offset_number = 0,
		rowwise_lettering = False,
		distrow = None,
		dpi = None,
		**kw
	):

		if dpi is None:
			dpi = 150
		self.dpi = dpi

		if figw_inches is None:
			figw_inches = 6.5

		if base_fontsize is None:
			base_fontsize = 9
		self.base_fontsize = base_fontsize

		self.add_lettering = add_lettering
		self.rowwise_lettering = rowwise_lettering
		self.letter_format = letter_format
		self.letter_offset_number = letter_offset_number
		if letter_fontsize is None:
			letter_fontsize = base_fontsize
		self.letter_fontsize = letter_fontsize
		self.letter_fontweight = letter_fontweight
		if letter_offsetx_inches is None:
			letter_offsetx_inches = 0.01
		self.letter_offsetx_inches = letter_offsetx_inches
		if letter_offsety_inches is None:
			letter_offsety_inches = 0.02
		self.letter_offsety_inches = letter_offsety_inches

		defaults = {
			'margintop_inches': 0.28,
			'marginleft_inches': 0.5,
			'marginright_inches': 0.1,
			'marginbottom_inches': 0.35
		}

		if kind is not None and kind == 'map':
			defaults['margintop_inches'] = 0.25
			defaults['marginleft_inches'] = 0.05
			defaults['marginright_inches'] = 0.05
			defaults['marginbottom_inches'] = 0.05

		d = {}
		for k,v in defaults.items():
			try:
				d[k] = kw[k]
			except:
				d[k] = v

				# cbar_height_inches = .1,
				# cbar_bottompadding_inches = .22,
				# cbar_toppadding_inches = 0.04
				# ''
		try:
			show_cbar = kw['show_cbar']
		except:
			show_cbar = True
		if show_cbar:
			total_cbar_width_inches = nbr_of_cbars*(cbar_leftpadding_inches+cbar_rightpadding_inches+cbar_width_inches)
			total_cbar_height_inches = nbr_of_cbars*(cbar_toppadding_inches+cbar_bottompadding_inches+cbar_height_inches)
		else:
			total_cbar_width_inches = 0
			total_cbar_height_inches = 0

		if nx is None:
			if nbr_of_panels is None or nbr_of_panels == 1:
				nx = 1
			else:
				nx = 2
		if ny is None:
			if nbr_of_panels is None or nbr_of_panels == 1:
				ny = 1
			else:
				ny = np.ceil((1.0 * nbr_of_panels)) / nx

		if distrow is None:
			distrow = ny-1
		self.distrow = distrow

		if aspectratiobyrow is None:
			aspectratiobyrow = [aspectratio]*int(ny)

		if nbr_of_panels is None:
			nbr_of_panels = nx * ny
		self.nbr_of_panels = nbr_of_panels

		if figw_inches is not None:
			#axw_inches = (figw_inches-figmarginleft_inches) / (1.0 * nx) - marginleft_inches - marginright_inches
			axw_inches = (figw_inches-figmarginleft_inches-total_cbar_width_inches) / (1.0 * nx) - d['marginleft_inches'] - d['marginright_inches']
		else:
			if axw_inches is not None:
				figw_inches = nx * (axw_inches + d['marginleft_inches'] + d['marginright_inches']) + figmarginleft_inches + total_cbar_width_inches
			if axh_inches is None:
				axh_inches = axw_inches / aspectratio

		if figh_inches is not None:
			sys.exit('figh_inches given...')
			if axh_inches is None:
				#axh_inches = figh_inches / (1.0 * ny) - margintop_inches - marginbottom_inches - cbar_bottompadding_inches - cbar_height_inches
				axh_inches = (figh_inches-total_cbar_height_inches-title_height_inches) / (1.0 * ny) - d['margintop_inches'] - d['marginbottom_inches']
			if figw_inches is None:
				axw_inches = axh_inches * aspectratio
				figw_inches = nx * (axw_inches + d['marginleft_inches'] + d['marginright_inches']) + figmarginleft_inches + total_cbar_width_inches
		else:
			axh_inches = axw_inches / aspectratio
			axh_inchesbyrow = [axw_inches / asp for asp in aspectratiobyrow]
			figh_inches = ny * axh_inches
			#figh_inches = np.sum(axh_inchesbyrow)
			figh_inches += ny * (d['margintop_inches'] + d['marginbottom_inches'])
			figh_inches += total_cbar_height_inches + title_height_inches

		aspectratio = axw_inches / axh_inches
		self.figh_inches = figh_inches
		self.figw_inches = figw_inches
		self.axh_inches = axh_inches
		self.axh_inchesbyrow = axh_inchesbyrow
		self.axw_inches = axw_inches

		if False:
		  print("New SubplotFigure:")
		  print(("  nx: %s" %nx))
		  print(("  ny: %s" %ny))
		  print(("  aspectratio: %s" %aspectratio))
		  print(("  aspectratiobyrow: %s" %aspectratiobyrow))
		  print(("  figw_inches: %s" %figw_inches))
		  print(("  figh_inches: %s" %figh_inches))
		  print(("  axw_inches: %s" %axw_inches))
		  print(("  axh_inches: %s" %axh_inches))
		  print(("  axh_inchesbyrow: %s" %axh_inchesbyrow))
		  print(("  marginleft_inches: %s" %marginleft_inches))
		  print(("  marginright_inches: %s" %marginright_inches))
		  print(("  margintop_inches: %s" %margintop_inches))
		  print(("  marginbottom_inches: %s" %marginbottom_inches))
		  
		self.figmarginleft = figmarginleft_inches / figw_inches
		self.marginleft = d['marginleft_inches'] / figw_inches
		self.marginright = d['marginright_inches'] / figw_inches
		self.margintop = d['margintop_inches'] / figh_inches
		self.marginbottom = d['marginbottom_inches'] / figh_inches
		self.title_height = title_height_inches / figh_inches
		self.cbar_width = cbar_width_inches / figw_inches
		self.cbar_height = cbar_height_inches / figh_inches
		self.cbar_rightpadding = cbar_rightpadding_inches / figw_inches
		self.cbar_bottompadding = cbar_bottompadding_inches / figh_inches
		self.cbar_leftpadding = cbar_leftpadding_inches / figw_inches
		self.cbar_toppadding = cbar_toppadding_inches / figh_inches
		self.total_cbar_width = total_cbar_width_inches / figw_inches
		self.total_cbar_height = total_cbar_height_inches / figh_inches
		self.cbar_width_percent = cbar_width_percent
		self.nbr_of_cbars = nbr_of_cbars
		self.cbars_drawn = 0
		self.axwtot = (1.-self.figmarginleft-self.total_cbar_width)/nx
		self.axw = self.axwtot - self.marginleft - self.marginright
		#self.axh = 1./ny - self.margintop - self.marginbottom - self.cbar_bottompadding - self.cbar_height
		self.axh = (1.-self.total_cbar_height-self.title_height)/ny - self.margintop - self.marginbottom
		self.nx = nx
		self.ny = ny
		self.fig = plt.figure(figsize = (figw_inches, figh_inches,), dpi = self.dpi)
		self.d = d

	def gettitlepos(self, inches = 0.04, row = 0):
		return 1. + inches / self.axh_inches
		#return 1. + inches / self.axh_inchesbyrow[row]

	def axtitle(self,t,alignleft=False,x0=None,**kw):
		y = self.gettitlepos()
		ok = False
		if alignleft:
			if x0 is None:
				x0 = 0.05
			plt.text(x0,y,t,
				horizontalalignment='left',
				verticalalignment='bottom',
				transform=self.ax.transAxes,
				**kw
			)
			ok = True
		if not ok:
			plt.text(0.5,y,t,
				horizontalalignment='center',
				verticalalignment='bottom',
				transform=self.ax.transAxes,
				**kw
			)

	def axylab(self,t,inches = 0.04,**kw):
		xpos = - (inches / self.axw_inches)
		plt.text(xpos,0.5,t,
			horizontalalignment='right',
			verticalalignment='center',
			rotation = 'vertical',
			transform=self.ax.transAxes,
			**kw
		)

	def title(self, t, **kw):
		if not 'fontweight' in kw:
			kw['fontweight'] = 450
		ypos = 1.-0.5*self.title_height
		w = (1.-self.figmarginleft-self.marginleft-self.marginright-self.total_cbar_width)
		xpos = self.figmarginleft+self.marginleft+w/2.
		if 1:
			plt.figtext(xpos,ypos,t,
				horizontalalignment='center',
				verticalalignment='center',
				#transform=self.fig.transAxes,
				**kw
			)
		else:
			self.fig.suptitle(
				text, 
				#fontsize = fontsize,
				verticalalignment = 'center',
				y = ypos,
				**kw
			)
		# ax = plt.gca()
		# a = self.fig.add_axes((
		# 	0,
		# 	1.-self.title_height,
		# 	1.,
		# 	0,
		# ))
		# plt.axis('off')
		# plt.title(text, fontsize = fontsize)
		# plt.sca(ax)

	def get_cbar_dims(self, left=None):
		bottom = self.cbar_bottompadding + self.cbars_drawn*self.total_cbar_height/self.nbr_of_cbars
		totalwidth = 1.-self.marginleft-self.marginright
		if self.cbar_width_percent is None:
			#if desc is None:
			self.cbar_width_percent = 100.
			#else:
			#	self.cbar_width_percent = 60.
		shrink = totalwidth * (100.-self.cbar_width_percent) / 100.
		#print(shrink,totalwidth,self.cbar_width_percent)
		if left is None:
			width = totalwidth - shrink
			#left = self.marginleft + shrink*0.5
			left = self.marginleft
			#left = self.marginleft + 
			#print(left)
		else:
			width = totalwidth - shrink - left + self.marginleft
		return {
			'bottom': bottom,
			'left': left,
			'width': width,
			'height': self.cbar_height,
			'totalwidth': totalwidth,
			'shrink': shrink
		}


	def draw_colorbar(self, 
		cmap = None, 
		fontsize = None, 
		ticks = None,
		fmt = None, 
		vmax = None, 
		vmin = None, 
		desc = None,
		number_of_cbar_ticks = None,
		alpha = None,
		extend = None,
		left = None,
		rightmargin = 0,
		top = None
		#center_colorbar = True
	):
		if extend is None:
			extend = 'neither'
		ax = plt.gca()
		if self.cbar_width>0:
			orientation = 'vertical'
			right = self.cbar_rightpadding + self.cbars_drawn*self.total_cbar_width/self.nbr_of_cbars
			left = 1. - right - self.cbar_width
			top = self.margintop+self.title_height
			height = 1.-top-self.marginbottom
			bottom = 1. - top - height

			if desc is not None:
				dpi = 72.
				#dpi = self.dpi
				if 1:
					a = self.fig.text(
						1 - 0.15 / self.figw_inches,
						1. - top - height/2.,
						#left,
						#1. - top + air,
						desc, 
						rotation = 'vertical',
						va = 'center',
						ha = 'left',
						fontsize = fontsize
					)

				else:
					# Find width of text:
					#bb = matplotlib.textpath.TextPath((0,0),desc,size=fontsize).get_extents()
					#bh = bb.height / self.figh_inches / dpi
					air = 4. / self.figh_inches / dpi
					a = self.fig.text(
						#left + self.cbar_width/2.,
						left,
						1. - top + air,
						desc, 
						ha = 'left',
						va = 'bottom',
						fontsize = fontsize
					)

			cax = self.fig.add_axes((
				left,
				bottom,
				self.cbar_width,
				height,
			))
		else:
			orientation = 'horizontal'
			# bottom = self.cbar_bottompadding + self.cbars_drawn*self.total_cbar_height/self.nbr_of_cbars
			# totalwidth = 1.-self.marginleft-self.marginright
			# if self.cbar_width_percent is None:
			# 	#if desc is None:
			# 	self.cbar_width_percent = 100.
			# 	#else:
			# 	#	self.cbar_width_percent = 60.
			# shrink = totalwidth * (100.-self.cbar_width_percent) / 100.
			# #print(shrink,totalwidth,self.cbar_width_percent)
			# if left is None:
			# 	width = totalwidth - shrink
			# 	#left = self.marginleft + shrink*0.5
			# 	left = self.marginleft
			# 	#left = self.marginleft + 
			# 	#print(left)
			# else:
			# 	width = totalwidth - shrink - left + self.marginleft
			dims = self.get_cbar_dims(left=left)
			left = dims['left']
			height = dims['height']
			bottom = dims['bottom']
			width = dims['width']

			if desc is not None:
				dpi = 72.
				#dpi = self.dpi
				# Find width of text:
				bb = matplotlib.textpath.TextPath((0,0),desc,size=fontsize).get_extents()
				bw = bb.width / self.figw_inches / dpi
				#air = totalwidth*0.02
				air = 4. / self.figw_inches / dpi
				#print(bb.width,bw,left,bw+air*2)
				if 1:
					left = self.marginleft+bw+air*2
					width = dims['totalwidth']-bw-air*3-rightmargin-dims['shrink']
					#if bw>left+air*2:
					#	width += left 
					#	left = bw+air
					#	width -= left 
				else:
					ww = air + bw
					#print(bb.width,width,ww,)
					width -= ww
					left += ww 
				#left = 1. - self.marginright - width - air
				a = self.fig.text(
					#0.5*(left+self.marginleft+air),
					left-air,
					bottom + 0.5*self.cbar_height,
					desc, 
					ha = 'right',
					va = 'center',
					fontsize = fontsize
				)
			if 0:
				if desc is not None:
					air = totalwidth*0.05
					left = 1. - self.marginright - width - air
					a = self.fig.text(
						#0.5*(left+self.marginleft+air),
						left-air/2.,
						bottom + 0.5*self.cbar_height,
						desc, 
						ha = 'right',
						va = 'center',
						fontsize = fontsize
					)
				else:
					left = self.marginleft + shrink*0.5
			cax = self.fig.add_axes((
				left,
				bottom,
				width,
				height,
			))

		if alpha is not None:
			my_cmap = cmap(np.arange(cmap.N))
			# Define the alphas
			alphas = np.linspace(0, 1, cmap.N)
			# Define the background
			BG = np.asarray([1., 1., 1.,])
			# Mix the colors with the background
			for i in range(cmap.N):
			    my_cmap[i,:-1] = my_cmap[i,:-1] * alpha + BG * (1.-alpha)
			# Create new colormap
			cmap = ListedColormap(my_cmap)

		cb = ColorbarBase(
			cax, 
			cmap=cmap, 
			orientation=orientation, 
			ticks = ticks, 
			format = fmt,
			norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax),
			extend = extend
		)
		if ticks is None and number_of_cbar_ticks is not None:
			from matplotlib import ticker
			tick_locator = ticker.MaxNLocator(nbins=number_of_cbar_ticks)
			cb.locator = tick_locator
			cb.update_ticks()

		#plt.colorbar(orientation='horizontal',cax=cax, ticks=ticks)
		if fontsize is not None:
			cax.tick_params(labelsize=fontsize-2)
		self.cbars_drawn += 1
		plt.sca(ax)

	def subplot(self, 
		i = 0, 
		letter = None, 
		offsetx_inches = None, 
		offsety_inches = None,
		proj = None,
		marginleft = None,
		frameon=None
	):
		if offsetx_inches is None:
			offsetx_inches = self.letter_offsetx_inches
			#offset_x_inches = self.axw_inches / 25.
		if offsety_inches is None:
			offsety_inches = self.letter_offsety_inches
			#offset_y_inches = self.axh_inches / 25.
		if marginleft is None:
			marginleft = self.marginleft
		#print 'Width, height:', self.axw_inches, self.axh_inches

		# Special case for last row
		row = int(np.floor((1.*i)/self.nx))
		col = i%self.nx
		addx = 0.
		if row==self.distrow and self.nbr_of_panels<self.nx*self.ny:
			#addx = (self.nx*self.ny-self.nbr_of_panels)*.5/self.nx
			addx = (self.nx*self.ny-self.nbr_of_panels)*self.axwtot/2.
		#print(row,self.ny,self.nbr_of_panels,self.nx*self.ny,addx)

		xpos = addx + self.axwtot * (i%self.nx) + marginleft + self.figmarginleft
		boxh = (1.-self.total_cbar_height-self.title_height)/self.ny
		ypos = 1. - boxh * (row+1) + self.marginbottom - self.title_height
		#ypos = 1. -  1./self.ny * np.floor(0.5*(i+self.nx)) + self.marginbottom
		#print("%i: xpos = %s, ypos = %s" %(i, xpos, ypos))
		if frameon is None:
			frameon = True
		axw = self.axw - marginleft + self.marginleft
		ax = self.fig.add_axes([xpos, ypos, axw, self.axh],projection=proj,frameon=frameon)#, aspect = aspectratio)
		#ax = self.fig.add_axes([xpos, ypos, self.axw, self.axh],projection=proj,frameon=frameon)#, aspect = aspectratio)
		if self.add_lettering:
			ok = True
			lnbr = i
			if self.rowwise_lettering:
				if col>0:
					ok = False
				else:
					lnbr = row
			if ok:
				lnbr += self.letter_offset_number
				if letter is None:
					letter = LETTERS[lnbr]
				t = self.letter_format %letter
				#print(offsetx_inches, offsety_inches)
				#print xpos, xpos-self.marginleft+offsetx_inches/self.axw_inches
				#print ypos,offsety_inches,self.axh_inches
				plt.figtext(
					xpos-marginleft+offsetx_inches/self.figw_inches,
					ypos+self.axh+self.margintop-offsety_inches/self.figh_inches,
					#ypos+self.axh,
					t,
					fontsize = self.letter_fontsize,
					fontweight = self.letter_fontweight,
					horizontalalignment='left',
					verticalalignment='top'
				)
		self.ax = ax
		return ax

