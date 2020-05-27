#!/usr/bin/env python

import sys
import os 
from datetime import datetime

import inkex
import shapes as shapes_pkg
from shapes import point_generator

class plotgcode(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)

        self.OptionParser.add_option('-w', 
          '--pen-up', 
          action = 'store',type = 'int', 
          dest = 'pen_up', 
          default = 26, 
          help = 'Pen Up')

        self.OptionParser.add_option('-x', 
          '--pen-down', 
          action = 'store',type = 'int', 
          dest = 'pen_down', 
          default = 5, 
          help = 'Pen Down')

        self.OptionParser.add_option('-a', 
          '--pen-rate', 
          action = 'store',type = 'int', 
          dest = 'pen_rate', 
          default = 3200, 
          help = 'Pen Rate')

        self.OptionParser.add_option('-t', 
          '--feed-rate-up', 
          action = 'store',type = 'int', 
          dest = 'feed_rate_up', 
          default = 3200, 
          help = 'Feed Rate Pen Up')

        self.OptionParser.add_option('-s', 
          '--feed-rate-down', 
          action = 'store',type = 'int', 
          dest = 'feed_rate_down', 
          default = 3200, 
          help = 'Feed Rate Pen Down')

        self.OptionParser.add_option('-i', 
          '--does-dip', 
          action = 'store',type = 'inkbool', 
          dest = 'does_dip', 
          default = False, 
          help = 'Intersperse paint dipping before shapes?')

        self.OptionParser.add_option('-y', 
          '--dip-when', 
          action = 'store', 
          type = 'int', 
          dest = 'dip_when', 
          default = 1, 
          help = 'How many shapes before paint dip? (First dip happens before first shape)')

        self.OptionParser.add_option('-p', 
          '--preamble', 
          action = 'store',type = 'string', 
          dest = 'preamble', 
          default = 'G21(Set to mm)', 
          help = 'Preamble G-code')

        self.OptionParser.add_option('-q', 
          '--postamble', 
          action = 'store',type = 'string', 
          dest = 'postamble', 
          default = 'z', 
          help = 'Postamble G-code')

        self.OptionParser.add_option('-o', 
          '--gcode-file', 
          action = 'store',type = 'string', 
          dest = 'gcode_file', 
          default = '/home/pi/Documents/gcode/', 
          help = 'The generated gcode file path + random #')
        
    def generate_gcode(self, svg):
        now = datetime.now() # current date and time
        now_time = now.strftime("%m-%d-%Y-%H:%M:%S") 
        gcode_file = os.path.join(os.path.expanduser('~'), self.options.gcode_file + now_time + ".gcode")
        try:
            os.remove(gcode_file)
        except OSError:
            pass

        pen_up = self.options.pen_up
        pen_down = self.options.pen_down
        feed_rate_up = self.options.feed_rate_up
        feed_rate_down = self.options.feed_rate_down
        pen_rate = self.options.pen_rate

        does_dip = self.options.does_dip
        dip_when = self.options.dip_when
        dip_count = dip_when
        
        width = svg.get('width')
        height = svg.get('height')
        inkex.debug(width)

        width = self.unittouu(width)
        height = self.unittouu(height)

        # if width > bed_width or height > bed_height:
        #     raise ValueError(('The document size (%d x %d) is greater than the bedsize' % 
        #                      (round(width, 1), round(height, 1)))) 

        with open(gcode_file, 'w') as gcode:  
            gcode.write(self.options.preamble + '\n')
            gcode.write("G00 Z%0.1f(Pen up)\n" % (pen_up))
     
            svg_shapes = set(['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path'])
            
            for elem in svg.iter():
                inkex.debug(elem)
                inkex.debug(elem.tag)
                try:
                    _, tag_suffix = elem.tag.split('}')
                except ValueError:
                    continue

                if tag_suffix in svg_shapes:
                    shape_class = getattr(shapes_pkg, tag_suffix)
                    shape_obj = shape_class(elem)
                    d = shape_obj.d_path()
                    m = shape_obj.transformation_matrix()

                    if d:
                        p = point_generator(d, m, 0.05)
                        preamble = True # hack!!
                        first = True
                        if does_dip and dip_count == dip_when:
                            gcode.write('G00 X100.0 Y0.0 F3200.0(Go to paint)\n')
                            gcode.write('G01 Z0.0 F3200.0(Pen down in paint)\n')
                            gcode.write('G00 X105.0 Y5.0 F1200.0(Move in paint)\n')
                            gcode.write("G00 Z%0.1f F3200.0(Pen up in paint)\n" % (pen_up))
                            dip_count = 0
                        else:
                          dip_count = dip_count + 1
                        for x,y in p:
                          if preamble:
                            gcode.write("G00 X%0.1f Y%0.1f F%0.1f(New shape)\n" % (x, y, feed_rate_up))
                            gcode.write("G01 Z%0.1f F%0.1f(Pen down)\n" % (pen_down, pen_rate))
                            preamble = False
                          else:
                            if first:
                              gcode.write("G01 X%0.1f Y%0.1f Z%0.1f F%0.1f\n" % (x, y, pen_down, feed_rate_down)) 
                              first = False
                            else:
                              gcode.write("G01 X%0.1f Y%0.1f Z%0.1f\n" % (x, y, pen_down)) 
                          
                        gcode.write("G01 Z%0.1f F%0.1f(Pen up)\n" % (pen_up, pen_rate))
                        # gcode.write(self.options.shape_postamble + '\n')

            gcode.write('G00 X0.0 Y0.0 F3200.0(Go home)\n')
            gcode.write('G01 Z0.0 F3200.0(Pen down)\n')
            # gcode.write(self.options.postamble + '\n')

    def effect(self):
        svg = self.document.getroot()
        self.generate_gcode(svg)

effect = plotgcode()
effect.affect()


