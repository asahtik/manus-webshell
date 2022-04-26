
try:
    import calmjs.toolchain
    from calmjs.webpack.toolchain import WebpackToolchain

    def builder():
        return WebpackToolchain()


except ImportError:
        pass

