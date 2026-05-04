{
    "patcher" : {
        "boxes" : [
            {
                "box" : {
                    "id" : "obj-1",
                    "maxclass" : "live.thisdevice",
                    "numinlets" : 0,
                    "numoutlets" : 1,
                    "outlettype" : ["bang"],
                    "patching_rect" : [20, 20, 100, 23],
                    "saved_attribute_attributes" : {
                        "valueof" : {
                            "name" : "clavus"
                        }
                    }
                }
            },
            {
                "box" : {
                    "id" : "obj-2",
                    "maxclass" : "comment",
                    "text" : "~▼~ clavus  —  Git for Ableton",
                    "patching_rect" : [20, 60, 260, 30],
                    "numoutlets" : 0
                }
            },
            {
                "box" : {
                    "id" : "obj-3",
                    "maxclass" : "live.text",
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["symbol"],
                    "patching_rect" : [20, 100, 120, 22],
                    "saved_attribute_attributes" : {
                        "valueof" : {
                            "expression" : "thisdevice_songname"
                        }
                    }
                }
            },
            {
                "box" : {
                    "id" : "obj-4",
                    "maxclass" : "message",
                    "text" : "ping",
                    "numinlets" : 2,
                    "numoutlets" : 1,
                    "outlettype" : [""],
                    "patching_rect" : [20, 140, 50, 18]
                }
            },
            {
                "box" : {
                    "id" : "obj-5",
                    "maxclass" : "js",
                    "text" : "clavus-api.js",
                    "numinlets" : 1,
                    "numoutlets" : 4,
                    "outlettype" : ["int", "", "", ""],
                    "patching_rect" : [100, 140, 130, 23]
                }
            },
            {
                "box" : {
                    "id" : "obj-6",
                    "maxclass" : "newobj",
                    "text" : "maxurl 2",
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["symbol"],
                    "patching_rect" : [260, 140, 100, 22]
                }
            },
            {
                "box" : {
                    "id" : "obj-7",
                    "maxclass" : "pattr",
                    "numinlets" : 1,
                    "numoutlets" : 0,
                    "patching_rect" : [20, 190, 60, 22],
                    "saved_attribute_attributes" : {
                        "valueof" : {
                            "name" : "clavus_project",
                            "reach" : 1
                        }
                    }
                }
            },
            {
                "box" : {
                    "id" : "obj-8",
                    "maxclass" : "button",
                    "numinlets" : 1,
                    "numoutlets" : 2,
                    "outlettype" : ["bang", "int"],
                    "patching_rect" : [20, 250, 30, 30]
                }
            },
            {
                "box" : {
                    "id" : "obj-9",
                    "maxclass" : "comment",
                    "text" : "📸 Snapshot",
                    "patching_rect" : [60, 255, 80, 16],
                    "numoutlets" : 0
                }
            },
            {
                "box" : {
                    "id" : "obj-10",
                    "maxclass" : "message",
                    "text" : "snapshot $1 $2",
                    "numinlets" : 2,
                    "numoutlets" : 1,
                    "outlettype" : [""],
                    "patching_rect" : [20, 300, 120, 18]
                }
            },
            {
                "box" : {
                    "id" : "obj-11",
                    "maxclass" : "live.remote",
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["int"],
                    "patching_rect" : [160, 250, 120, 22],
                    "saved_attribute_attributes" : {
                        "valueof" : {
                            "parameter_longname" : "live_set current_song current_song_time"
                        }
                    }
                }
            },
            {
                "box" : {
                    "id" : "obj-12",
                    "maxclass" : "number",
                    "numinlets" : 1,
                    "numoutlets" : 2,
                    "outlettype" : ["int", "list"],
                    "patching_rect" : [160, 290, 80, 22]
                }
            },
            {
                "box" : {
                    "id" : "obj-13",
                    "maxclass" : "newobj",
                    "text" : "tobars-beats-sixteenths",
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["symbol"],
                    "patching_rect" : [160, 330, 140, 22]
                }
            },
            {
                "box" : {
                    "id" : "obj-14",
                    "maxclass" : "message",
                    "text" : "snapshot $2 $1",
                    "numinlets" : 2,
                    "numoutlets" : 1,
                    "outlettype" : [""],
                    "patching_rect" : [20, 370, 140, 18]
                }
            },
            {
                "box" : {
                    "id" : "obj-15",
                    "maxclass" : "button",
                    "numinlets" : 1,
                    "numoutlets" : 2,
                    "outlettype" : ["bang", "int"],
                    "patching_rect" : [20, 440, 30, 30]
                }
            },
            {
                "box" : {
                    "id" : "obj-16",
                    "maxclass" : "comment",
                    "text" : "📍 Mark Cue",
                    "patching_rect" : [60, 445, 80, 16],
                    "numoutlets" : 0
                }
            },
            {
                "box" : {
                    "id" : "obj-17",
                    "maxclass" : "message",
                    "text" : "addcuetrack $1 $2 $3",
                    "numinlets" : 2,
                    "numoutlets" : 1,
                    "outlettype" : [""],
                    "patching_rect" : [20, 490, 160, 18]
                }
            },
            {
                "box" : {
                    "id" : "obj-18",
                    "maxclass" : "live.remote",
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["symbol"],
                    "patching_rect" : [200, 440, 140, 22],
                    "saved_attribute_attributes" : {
                        "valueof" : {
                            "parameter_longname" : "live_set current_song view selected_track name"
                        }
                    }
                }
            },
            {
                "box" : {
                    "id" : "obj-19",
                    "maxclass" : "message",
                    "text" : "; addcue $1 $2 $3",
                    "patching_rect" : [200, 490, 140, 18],
                    "numinlets" : 2,
                    "numoutlets" : 1,
                    "outlettype" : [""]
                }
            },
            {
                "box" : {
                    "id" : "obj-20",
                    "maxclass" : "dl",
                    "text" : "press shift + click for cue with text input",
                    "patching_rect" : [20, 540, 320, 100],
                    "numoutlets" : 0
                }
            },
            {
                "box" : {
                    "id" : "obj-21",
                    "maxclass" : "button",
                    "numinlets" : 1,
                    "numoutlets" : 2,
                    "outlettype" : ["bang", "int"],
                    "patching_rect" : [20, 670, 30, 30]
                }
            },
            {
                "box" : {
                    "id" : "obj-22",
                    "maxclass" : "comment",
                    "text" : "📌 Inject Markers",
                    "patching_rect" : [60, 675, 100, 16],
                    "numoutlets" : 0
                }
            },
            {
                "box" : {
                    "id" : "obj-23",
                    "maxclass" : "message",
                    "text" : "inject $1",
                    "numinlets" : 2,
                    "numoutlets" : 1,
                    "outlettype" : [""],
                    "patching_rect" : [20, 720, 80, 18]
                }
            },
            {
                "box" : {
                    "id" : "obj-24",
                    "maxclass" : "button",
                    "numinlets" : 1,
                    "numoutlets" : 2,
                    "outlettype" : ["bang", "int"],
                    "patching_rect" : [20, 790, 30, 30]
                }
            },
            {
                "box" : {
                    "id" : "obj-25",
                    "maxclass" : "comment",
                    "text" : "↩ Restore",
                    "patching_rect" : [60, 795, 80, 16],
                    "numoutlets" : 0
                }
            },
            {
                "box" : {
                    "id" : "obj-26",
                    "maxclass" : "message",
                    "text" : "restore $1",
                    "numinlets" : 2,
                    "numoutlets" : 1,
                    "outlettype" : [""],
                    "patching_rect" : [20, 840, 80, 18]
                }
            },
            {
                "box" : {
                    "id" : "obj-27",
                    "maxclass" : "message",
                    "text" : "ping",
                    "numinlets" : 2,
                    "numoutlets" : 1,
                    "outlettype" : [""],
                    "patching_rect" : [20, 920, 50, 18]
                }
            },
            {
                "box" : {
                    "id" : "obj-28",
                    "maxclass" : "newobj",
                    "text" : "metro 5000",
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["bang"],
                    "patching_rect" : [20, 950, 90, 22]
                }
            },
            {
                "box" : {
                    "id" : "obj-29",
                    "maxclass" : "button",
                    "numinlets" : 1,
                    "numoutlets" : 2,
                    "outlettype" : ["bang", "int"],
                    "patching_rect" : [20, 980, 30, 30]
                }
            },
            {
                "box" : {
                    "id" : "obj-30",
                    "maxclass" : "comment",
                    "text" : "Toggle auto-ping",
                    "patching_rect" : [60, 985, 100, 16],
                    "numoutlets" : 0
                }
            },
            {
                "box" : {
                    "id" : "obj-31",
                    "maxclass" : "comment",
                    "text" : "── Status ──",
                    "patching_rect" : [20, 1040, 100, 16],
                    "numoutlets" : 0
                }
            },
            {
                "box" : {
                    "id" : "obj-32",
                    "maxclass" : "newobj",
                    "text" : "dict clavus_ping_rsp",
                    "patching_rect" : [20, 1080, 140, 22],
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["dict"]
                }
            },
            {
                "box" : {
                    "id" : "obj-33",
                    "maxclass" : "newobj",
                    "text" : "dict clavus_snap_rsp",
                    "patching_rect" : [200, 1080, 140, 22],
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["dict"]
                }
            },
            {
                "box" : {
                    "id" : "obj-34",
                    "maxclass" : "newobj",
                    "text" : "dict clavus_cues_rsp",
                    "patching_rect" : [380, 1080, 140, 22],
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["dict"]
                }
            },
            {
                "box" : {
                    "id" : "obj-35",
                    "maxclass" : "newobj",
                    "text" : "dict clavus_restore_rsp",
                    "patching_rect" : [560, 1080, 150, 22],
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["dict"]
                }
            },
            {
                "box" : {
                    "id" : "obj-36",
                    "maxclass" : "newobj",
                    "text" : "dict clavus_inject_rsp",
                    "patching_rect" : [750, 1080, 140, 22],
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["dict"]
                }
            },
            {
                "box" : {
                    "id" : "obj-37",
                    "maxclass" : "newobj",
                    "text" : "dict clavus_proj_rsp",
                    "patching_rect" : [20, 1130, 140, 22],
                    "numinlets" : 1,
                    "numoutlets" : 1,
                    "outlettype" : ["dict"]
                }
            }
        ],
        "lines" : [
            {"destination" : ["obj-4", 0], "source" : ["obj-1", 0]},
            {"destination" : ["obj-5", 0], "source" : ["obj-4", 0]},
            {"destination" : ["obj-5", 0], "source" : ["obj-3", 0]},
            {"destination" : ["obj-5", 0], "source" : ["obj-27", 0]},
            {"destination" : ["obj-6", 0], "source" : ["obj-5", 1]},
            {"destination" : ["obj-10", 0], "source" : ["obj-8", 0]},
            {"destination" : ["obj-12", 0], "source" : ["obj-11", 0]},
            {"destination" : ["obj-13", 0], "source" : ["obj-12", 0]},
            {"destination" : ["obj-14", 0], "source" : ["obj-13", 0]},
            {"destination" : ["obj-14", 1], "source" : ["obj-7", 0]},
            {"destination" : ["obj-5", 0], "source" : ["obj-14", 0]},
            {"destination" : ["obj-17", 0], "source" : ["obj-15", 0]},
            {"destination" : ["obj-17", 1], "source" : ["obj-7", 0]},
            {"destination" : ["obj-17", 2], "source" : ["obj-13", 0]},
            {"destination" : ["obj-17", 3], "source" : ["obj-18", 0]},
            {"destination" : ["obj-5", 0], "source" : ["obj-17", 0]},
            {"destination" : ["obj-23", 0], "source" : ["obj-21", 0]},
            {"destination" : ["obj-23", 1], "source" : ["obj-7", 0]},
            {"destination" : ["obj-5", 0], "source" : ["obj-23", 0]},
            {"destination" : ["obj-26", 0], "source" : ["obj-24", 0]},
            {"destination" : ["obj-26", 1], "source" : ["obj-7", 0]},
            {"destination" : ["obj-5", 0], "source" : ["obj-26", 0]},
            {"destination" : ["obj-27", 0], "source" : ["obj-28", 0]},
            {"destination" : ["obj-28", 0], "source" : ["obj-29", 0]}
        ],
        "appversion" : "8.6.5",
        "format" : "json",
        "rect" : [0, 0, 1000, 1230],
        "saved_object_attributes" : {
            "canvas_color" : 374131077,
            "rect" : [0, 0, 1000, 1230]
        },
        "version" : "2"
    }
}
