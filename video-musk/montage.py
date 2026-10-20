import sys, cairo
out = sys.argv[1]; files = sys.argv[2:]
cols = 2 if len(files) <= 4 else 3 if len(files) <= 9 else 4
rows = (len(files) + cols - 1) // cols
w, h = 960, 540
o = cairo.ImageSurface(cairo.FORMAT_RGB24, w * cols, h * rows)
c = cairo.Context(o)
for i, f in enumerate(files):
    s = cairo.ImageSurface.create_from_png(f)
    c.save(); c.translate((i % cols) * w, (i // cols) * h); c.scale(w / s.get_width(), h / s.get_height())
    c.set_source_surface(s, 0, 0); c.paint(); c.restore()
    c.set_source_rgb(1, 1, 0); c.select_font_face("Sans"); c.set_font_size(26); c.move_to((i % cols) * w + 12, (i // cols) * h + 32); c.show_text(f.split('_')[-1][:-4])
o.write_to_png(out)
