import functions
from functions import *

import inspect

def combinations(items, n):
	if n==0: yield []
	else:
		for i in xrange(len(items)):
			for cc in combinations(items[i+1:],n-1):
				yield [items[i]]+cc
	
# Simplify and hash all functions to not repeat
# Only thing is the hash takes a bunch of memory

class FunctionGenerator:
	def __init__(self, **attrs):
		if attrs.has_key('atoms'):
			self.atoms = attrs['atoms'][:]
		else:
			self.atoms = [Constant(i) for i in range(1, 10)] + \
				[Constant(-1)] + \
				[Variable('x_'+str(i)) for i in range(2)] + \
				[Variable('t')]

		if attrs.has_key('functions'):
			self.functions = attrs['functions'][:]
		else:
			g = [getattr(functions, f) for f in dir(functions)]
			self.functions = filter(lambda f : inspect.isclass(f) and
				issubclass(f, functions.Function), g)
		
	def __iter__(self):
		return self.next()
		
	def next(self):
		search = self.atoms[:]
		frontier = []

		while (len(search) > 0 or len(frontier) > 0):
			for s in search:
				for f in self.functions:
					if f.cardinality > 0:
						children = list(combinations(self.atoms, f.cardinality-1))
						if f.commutative:
							frontier.extend(map(lambda x : f(*x), 
								[[s] + c for c in children]))
						else:
							frontier.extend(map(lambda x : f(*x), 
								[[s] + c for c in children] +
								[c + [s] for c in children]))
					
				yield s
			
			search = frontier
			frontier = []
			
		raise StopIteration
		
#for f in filter(lambda f : Variable('t') in f, FunctionGenerator()):
#for f in FunctionGenerator():
#	if len(f) > 3:
#		break
		
#	if Variable('t') in f:
#		print f

x = Variable('x')
y = Variable('y')

f = (3*(x**2+y))
dfdx = Diff(f, x)
print 'f=%s' % f
print 'df/dx=%s' % dfdx.simplify()
